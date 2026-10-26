from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User, Company
from mrf.models import MRF, Department, Designation, WorkflowTemplate
from jobs.models import Job, JobApplication
from onboarding.models import OnboardingForm
from onboarding.utils.joining_check import run_joining_date_check


class JoiningCheckAndJourneyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(name="Test Company")
        self.dept = Department.objects.create(name="Engineering", company=self.company)
        self.designation = Designation.objects.create(
            name="Software Engineer",
            department=self.dept,
            key_responsibility="Writing code",
            required_qualifications="B.Tech",
            skills_competencies="Python",
        )
        self.workflow = WorkflowTemplate.objects.create(name="Standard Workflow", company=self.company)

        self.user_hr = User.objects.create(
            email="hr1@knowcraft.in",
            name="HR One",
            role="hr",
            company=self.company,
            is_active=True,
        )
        self.mrf = MRF.objects.create(
            company=self.company,
            mrf_name="Test MRF",
            department=self.dept,
            position_department=self.dept,
            designation=self.designation,
            team="Engineering",
            workflow_template=self.workflow,
            requested_by=self.user_hr,
            requested_by_name="HR One",
            requested_by_designation="HR",
            status="approved",
            no_of_vacancies=1,
            expected_date_of_joining=date.today() + timedelta(days=30),
            key_responsibility="Coding and testing",
            required_qualifications="B.Tech in Computer Science",
            skills_competencies="Python, Django, PostgreSQL",
            business_justification="New expansion",
            experience_range="2-5 years",
            salary_range="10-15 LPA",
        )
        self.job = Job.objects.filter(mrf=self.mrf).first()
        if not self.job:
            self.job = Job.objects.create(
                company=self.company,
                department=self.dept,
                mrf=self.mrf,
                job_title="Software Engineer",
                status="open",
                is_active=True,
                no_of_positions=1,
                positions_filled=0,
                key_responsibility="Writing code",
                assigned_to_internal_hr=self.user_hr,
            )
        else:
            self.job.assigned_to_internal_hr = self.user_hr
            self.job.save(update_fields=['assigned_to_internal_hr'])

        self.candidate = JobApplication.objects.create(
            job=self.job,
            candidate_name="John Doe",
            candidate_email="john@personal.com",
            work_email="",
            status="joining_pending",
            joining_date=date.today() - timedelta(days=1),
            hod_name="Dr. Smith",
            hod_email="smith@knowcraft.in",
            reporting_manager_name="Jane Doe",
            reporting_manager_email="jane@knowcraft.in",
            team_manager_name="Bob Brown",
            team_manager_email="bob@knowcraft.in",
        )
        self.onboarding_form = OnboardingForm.objects.create(
            job_application=self.candidate,
            personal_email_id="john@personal.com",
            first_name="John",
            last_name="Doe",
        )

    @patch("onboarding.utils.notifications.notify_internal")
    @patch("onboarding.utils.engine.automation_engine")
    def test_run_joining_date_check_missing_work_email(self, mock_engine, mock_notify):
        """Candidate on/after joining_date without work_email stays in joining_pending."""
        self.candidate.work_email = ""
        self.candidate.save()

        run_joining_date_check()

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, "joining_pending")
        mock_engine.assert_not_called()
        mock_notify.assert_called_once_with(self.candidate, "missing_work_email_reminder")

    @patch("onboarding.utils.joining_manager_email.send_joining_day_manager_email", return_value=True)
    def test_run_joining_date_check_with_work_email(self, mock_send_manager_email):
        """Candidate on/after joining_date with work_email transitions to joined."""
        self.candidate.work_email = "john@knowcraft.in"
        self.candidate.save()

        run_joining_date_check()

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.status, "joined")
        self.assertTrue(self.candidate.is_joining_day_manager_email_sent)
        mock_send_manager_email.assert_called_once()

    def test_onboarding_journey_milestones_and_candidate_fields(self):
        """Verify OnboardingJourneyAPI returns hod_assigned, reporting_manager_assigned milestones and candidate fields."""
        url = reverse("onboarding-journey", kwargs={"id": str(self.candidate.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        # Check candidate dict contains all manager fields
        candidate_data = data["candidate"]
        self.assertEqual(candidate_data["hod_name"], "Dr. Smith")
        self.assertEqual(candidate_data["hod_email"], "smith@knowcraft.in")
        self.assertEqual(candidate_data["reporting_manager_name"], "Jane Doe")
        self.assertEqual(candidate_data["reporting_manager_email"], "jane@knowcraft.in")
        self.assertEqual(candidate_data["team_manager_name"], "Bob Brown")
        self.assertEqual(candidate_data["team_manager_email"], "bob@knowcraft.in")

        # Check milestones
        milestones = {m["key"]: m for m in data["milestones"]}

        self.assertIn("hod_assigned", milestones)
        self.assertTrue(milestones["hod_assigned"]["completed"])
        self.assertEqual(milestones["hod_assigned"]["detail"], "Dr. Smith (smith@knowcraft.in)")
        self.assertEqual(milestones["hod_assigned"]["emails_sent"], "smith@knowcraft.in")

        self.assertIn("reporting_manager_assigned", milestones)
        self.assertTrue(milestones["reporting_manager_assigned"]["completed"])
        self.assertEqual(milestones["reporting_manager_assigned"]["detail"], "Jane Doe (jane@knowcraft.in)")
        self.assertEqual(milestones["reporting_manager_assigned"]["emails_sent"], "jane@knowcraft.in")

    def test_onboarding_journey_milestones_pending_when_empty(self):
        """Verify milestones are completed=False when fields are empty."""
        self.candidate.hod_name = None
        self.candidate.hod_email = None
        self.candidate.reporting_manager_name = ""
        self.candidate.reporting_manager_email = ""
        self.candidate.save()

        url = reverse("onboarding-journey", kwargs={"id": str(self.candidate.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        milestones = {m["key"]: m for m in data["milestones"]}

        self.assertFalse(milestones["hod_assigned"]["completed"])
        self.assertEqual(milestones["hod_assigned"]["detail"], "Pending assignment")

        self.assertFalse(milestones["reporting_manager_assigned"]["completed"])
        self.assertEqual(milestones["reporting_manager_assigned"]["detail"], "Pending assignment")

    @patch("onboarding.utils.notifications.send_email")
    def test_onboarding_notification_cc_internal_hrs_not_talent(self, mock_send_email):
        """Verify notify_candidate for onboarding stages CCs internal HRs and not talent@knowcraft.in."""
        from onboarding.utils.notifications import notify_candidate

        self.candidate.work_email = "john@knowcraft.in"
        self.candidate.status = "joined"
        self.candidate.save()

        notify_candidate(self.candidate, "d5_document_verification", cc=[])

        self.assertTrue(mock_send_email.called)
        call_kwargs = mock_send_email.call_args.kwargs
        self.assertEqual(call_kwargs["use_default_cc"], False)
        self.assertIn("hr1@knowcraft.in", call_kwargs["cc"])
        self.assertNotIn("talent@knowcraft.in", call_kwargs["cc"])
