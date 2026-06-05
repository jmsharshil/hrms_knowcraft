from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from datetime import date

from jobs.models import Job, JobApplication
from bgv.models import CandidateBGV
from bgv.services import initiate_bgv, is_fresher
from bgv.signals import (
    trigger_bgv_on_offer_accepted,
    update_bgv_schedule_on_joining_date_change,
    sync_bgv_status_to_application,
)
from bgv.tasks import run_bgv_schedule_check, run_bgv_status_poll
from accounts.models import Company, User
from mrf.models import Department, Designation, MRF, WorkflowTemplate


class BGVTests(TestCase):
    def setUp(self):
        # Setup required objects for JobApplication
        self.company = Company.objects.create(name='TestCo', email='co@test.com')
        self.admin = User.objects.create_user(
            email='admin@test.com', company=self.company, role='admin',
            password='pass', name='Admin User'
        )
        self.dept = Department.objects.create(name='Engineering', company=self.company)
        self.desig = Designation.objects.create(
            name='SDE', company=self.company, department=self.dept
        )
        self.wf = WorkflowTemplate.objects.create(
            name='Default', company=self.company, is_default=True
        )

        self.mrf = MRF.objects.create(
            company=self.company, mrf_name='Test MRF', department=self.dept,
            requested_by=self.admin, requested_by_name='Admin',
            requested_by_designation='CTO', designation=self.desig,
            team='Backend', position_department=self.dept,
            experience_range='2-5', business_justification='Need',
            salary_range='5-8 LPA', expected_date_of_joining=date.today(),
            workflow_template=self.wf, status='approved',
            key_responsibility='Code', required_qualifications='CS',
            skills_competencies='Python'
        )

        self.job = self.mrf.job

        self.application = JobApplication.objects.create(
            job=self.job,
            candidate_name="Test User",
            candidate_email="test@test.com",
            candidate_phone="9999999999",
            status="received",
            experience_years=2,
            joining_date=timezone.now().date() + timezone.timedelta(days=30)
        )

    # ------------------ SIGNALS & HELPERS TESTS ------------------ #

    @patch("bgv.signals.initiate_bgv")
    @patch("bgv.signals.is_fresher")
    def test_trigger_bgv_on_offer_accepted_fresher(self, mock_is_fresher, mock_initiate):
        """Test that BGV is initiated immediately for freshers."""
        mock_is_fresher.return_value = True
        self.application.status = "offer_accepted"

        trigger_bgv_on_offer_accepted(JobApplication, self.application, False)

        mock_is_fresher.assert_called_once_with(self.application)
        mock_initiate.assert_called_once_with(self.application)

    @patch("bgv.signals.initiate_bgv")
    @patch("bgv.signals.is_fresher")
    def test_trigger_bgv_on_offer_accepted_experienced(self, mock_is_fresher, mock_initiate):
        """Test that BGV is scheduled for experienced candidates."""
        mock_is_fresher.return_value = False
        self.application.status = "offer_accepted"

        trigger_bgv_on_offer_accepted(JobApplication, self.application, False)

        mock_is_fresher.assert_called_once_with(self.application)
        mock_initiate.assert_not_called()
        self.assertEqual(CandidateBGV.objects.count(), 1)
        bgv = CandidateBGV.objects.get()
        self.assertEqual(bgv.status, "pending_schedule")
        self.assertFalse(bgv.is_fresher)
        expected_date = self.application.joining_date - timezone.timedelta(days=15)
        self.assertEqual(bgv.bgv_scheduled_date, expected_date)

    @patch("bgv.signals.initiate_bgv")
    @patch("bgv.signals.is_fresher")
    def test_trigger_bgv_on_offer_accepted_no_joining_date(self, mock_is_fresher, mock_initiate):
        """Test that pending BGV is created when no joining date is set."""
        mock_is_fresher.return_value = False
        self.application.status = "offer_accepted"
        self.application.joining_date = None
        self.application.save()

        trigger_bgv_on_offer_accepted(JobApplication, self.application, False)

        mock_is_fresher.assert_called_once_with(self.application)
        mock_initiate.assert_not_called()
        self.assertEqual(CandidateBGV.objects.count(), 1)
        bgv = CandidateBGV.objects.get()
        self.assertEqual(bgv.status, "pending_schedule")
        self.assertFalse(bgv.is_fresher)
        self.assertIsNone(bgv.bgv_scheduled_date)

    def test_update_bgv_schedule_on_joining_date_change(self):
        """Test that BGV schedule is updated when joining date changes."""
        bgv = CandidateBGV.objects.create(
            candidate=self.application,
            status="pending_schedule",
            is_fresher=False,
            bgv_scheduled_date=self.application.joining_date - timezone.timedelta(days=30)
        )

        new_joining_date = self.application.joining_date + timezone.timedelta(days=10)
        self.application.joining_date = new_joining_date
        self.application.save()
        update_bgv_schedule_on_joining_date_change(JobApplication, self.application, False)

        bgv.refresh_from_db()
        expected_date = new_joining_date - timezone.timedelta(days=15)
        self.assertEqual(bgv.bgv_scheduled_date, expected_date)

    @patch("bgv.services._ongrid_request")
    def test_initiate_bgv_preserves_existing_individual_id_on_api_error(self, mock_request):
        """Failed initiate_bgv should not clear an existing OnGrid ID."""
        CandidateBGV.objects.create(
            candidate=self.application,
            status="in_progress",
            ongrid_individual_id="ind_12345"
        )
        mock_request.return_value = ({"message": "Service unavailable"}, 500, False)

        result = initiate_bgv(self.application)

        bgv = CandidateBGV.objects.get(candidate=self.application)
        self.assertEqual(result.ongrid_individual_id, "ind_12345")
        self.assertEqual(bgv.ongrid_individual_id, "ind_12345")
        self.assertEqual(bgv.status, "in_progress")
        self.assertIn("Preserving existing OnGrid individualId", bgv.remarks)

    def test_update_bgv_schedule_when_no_bgv(self):
        """Test that nothing happens when no pending BGV exists."""
        self.application.joining_date = timezone.now().date() + timezone.timedelta(days=30)
        self.application.save()

        update_bgv_schedule_on_joining_date_change(JobApplication, self.application, False)
        self.assertEqual(CandidateBGV.objects.count(), 0)

    @patch("bgv.signals.CandidateBGV.objects")
    def test_sync_bgv_status_to_application(self, mock_bgv_manager):
        """Test that BGV status is synced to application and approval note."""
        self.application.status = "offer_accepted"
        self.application.save()
        mock_bgv = MagicMock()
        mock_bgv.status = "initiated"
        mock_bgv.candidate = self.application
        mock_bgv_manager.get.return_value = mock_bgv

        sync_bgv_status_to_application(CandidateBGV, mock_bgv)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "bgv_initiated")

    @patch("bgv.signals.CandidateBGV.objects")
    def test_sync_bgv_status_to_application_different_status(self, mock_bgv_manager):
        """Test that BGV status is synced only when different."""
        self.application.status = "bgv_initiated"
        self.application.save()

        mock_bgv = MagicMock()
        mock_bgv.status = "initiated"
        mock_bgv.candidate = self.application
        mock_bgv_manager.get.return_value = mock_bgv

        sync_bgv_status_to_application(CandidateBGV, mock_bgv)
        self.assertEqual(self.application.status, "bgv_initiated")

    def test_is_fresher(self):
        """Test the is_fresher helper function for all edge cases."""
        app_fresher = JobApplication(experience_years=0.5)
        app_experienced = JobApplication(experience_years=3)
        app_zero = JobApplication(experience_years=0)
        app_none = JobApplication(experience_years=None)

        self.assertTrue(is_fresher(app_fresher))
        self.assertFalse(is_fresher(app_experienced))
        self.assertTrue(is_fresher(app_zero))
        self.assertTrue(is_fresher(app_none))

    # ------------------ BACKGROUND THREADS TESTS ------------------ #

    @patch("bgv.services.initiate_bgv")
    def test_run_bgv_schedule_check_past_date(self, mock_initiate_bgv):
        """Test background thread for schedule checking initiates BGV if date is past or today."""
        bgv = CandidateBGV.objects.create(
            candidate=self.application,
            status="pending_schedule",
            is_fresher=False,
            bgv_scheduled_date=date.today() - timezone.timedelta(days=1)
        )
        
        run_bgv_schedule_check()
        
        mock_initiate_bgv.assert_called_once_with(self.application)

    @patch("bgv.services.initiate_bgv")
    def test_run_bgv_schedule_check_future_date(self, mock_initiate_bgv):
        """Test background thread does not initiate BGV if date is in the future."""
        bgv = CandidateBGV.objects.create(
            candidate=self.application,
            status="pending_schedule",
            is_fresher=False,
            bgv_scheduled_date=date.today() + timezone.timedelta(days=10)
        )
        
        run_bgv_schedule_check()
        
        mock_initiate_bgv.assert_not_called()

    @patch("bgv.services.initiate_bgv")
    def test_run_bgv_schedule_check_no_date(self, mock_initiate_bgv):
        """Test background thread skips records with no schedule date."""
        bgv = CandidateBGV.objects.create(
            candidate=self.application,
            status="pending_schedule",
            is_fresher=False,
            bgv_scheduled_date=None
        )
        
        run_bgv_schedule_check()
        
        mock_initiate_bgv.assert_not_called()

    @patch("bgv.services.get_individual_status")
    @patch("bgv.services.get_verification_report")
    def test_run_bgv_status_poll_all_completed(self, mock_get_report, mock_get_individual):
        """Test background poller sets status to completed when all verifications are Clear/Completed."""
        bgv = CandidateBGV.objects.create(
            candidate=self.application,
            status="in_progress",
            ongrid_individual_id="ind_12345"
        )
        mock_get_report.return_value = {
            "verifications": [
                {"status": "Clear"},
                {"status": "Completed"}
            ]
        }
        mock_get_individual.return_value = {"reportUrl": "https://example.com/report"}

        run_bgv_status_poll()

        bgv.refresh_from_db()
        self.assertEqual(bgv.status, "completed")
        self.assertIsNotNone(bgv.completed_at)

    @patch("bgv.services.get_individual_status")
    @patch("bgv.services.get_verification_report")
    def test_run_bgv_status_poll_insufficient(self, mock_get_report, mock_get_individual):
        """Test background poller sets status to insufficient when DataInsufficient is present."""
        bgv = CandidateBGV.objects.create(
            candidate=self.application,
            status="in_progress",
            ongrid_individual_id="ind_12345"
        )
        mock_get_report.return_value = {
            "verifications": [
                {"status": "Clear"},
                {"status": "DataInsufficient"}
            ]
        }
        mock_get_individual.return_value = {}

        run_bgv_status_poll()

        bgv.refresh_from_db()
        self.assertEqual(bgv.status, "insufficient")

    @patch("bgv.services.get_individual_status")
    @patch("bgv.services.get_verification_report")
    def test_run_bgv_status_poll_in_progress(self, mock_get_report, mock_get_individual):
        """Test background poller keeps status in_progress if verifications are pending."""
        bgv = CandidateBGV.objects.create(
            candidate=self.application,
            status="initiated",
            ongrid_individual_id="ind_12345"
        )
        mock_get_report.return_value = {
            "verifications": [
                {"status": "Clear"},
                {"status": "Pending"}
            ]
        }
        mock_get_individual.return_value = {}

        run_bgv_status_poll()

        bgv.refresh_from_db()
        self.assertEqual(bgv.status, "in_progress")

    @patch("bgv.services.get_verification_report")
    def test_run_bgv_status_poll_no_verifications(self, mock_get_report):
        """Test background poller handles empty verifications list safely."""
        bgv = CandidateBGV.objects.create(
            candidate=self.application,
            status="initiated",
            ongrid_individual_id="ind_12345"
        )
        mock_get_report.return_value = {
            "verifications": []
        }

        run_bgv_status_poll()

        bgv.refresh_from_db()
        self.assertEqual(bgv.status, "initiated") # Should remain unchanged

    @patch("bgv.services.get_verification_report")
    def test_run_bgv_status_poll_no_ongrid_id(self, mock_get_report):
        """Test background poller skips candidates without an OnGrid individual ID."""
        bgv = CandidateBGV.objects.create(
            candidate=self.application,
            status="initiated",
            ongrid_individual_id=""
        )

        run_bgv_status_poll()

        mock_get_report.assert_not_called()
