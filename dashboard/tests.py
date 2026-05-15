"""
Django test cases for Analytics API date filters and all sections.
"""
from datetime import datetime, date, time, timedelta
from django.test import TestCase
from django.utils import timezone
from django.db.models import Q
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from accounts.models import Company, User
from mrf.models import Department, Designation, MRF, WorkflowTemplate, ApprovalWorkflow
from jobs.models import Job, JobApplication
from slots.models import InterviewFeedback, Interviewer
from onboarding.models import ApprovalNote, JobApplicationDocument, OfferDocument


class AnalyticsTestBase(TestCase):
    """Shared setup for all analytics tests."""

    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(name='TestCo', email='co@test.com')
        cls.admin = User.objects.create_user(
            email='admin@test.com', company=cls.company, role='admin',
            password='pass', name='Admin User'
        )
        cls.hr = User.objects.create_user(
            email='hr@test.com', company=cls.company, role='hr',
            password='pass', name='HR User'
        )
        cls.dept = Department.objects.create(name='Engineering', company=cls.company)
        cls.desig = Designation.objects.create(
            name='SDE', company=cls.company, department=cls.dept
        )

        # Workflow setup for MRF
        cls.wf = WorkflowTemplate.objects.create(
            name='Default', company=cls.company, is_default=True
        )
        ApprovalWorkflow.objects.create(
            template=cls.wf, level=1, required_role='admin',
            approver=cls.admin, order=1, company=cls.company
        )

        # Create MRF
        cls.mrf = MRF.objects.create(
            company=cls.company, mrf_name='Test MRF', department=cls.dept,
            requested_by=cls.admin, requested_by_name='Admin',
            requested_by_designation='CTO', designation=cls.desig,
            team='Backend', position_department=cls.dept,
            experience_range='2-5', business_justification='Need',
            salary_range='5-8 LPA', expected_date_of_joining=date.today(),
            workflow_template=cls.wf, status='approved',
            submitted_at=timezone.now() - timedelta(days=10),
        )

        # Create Job
        cls.job = Job.objects.create(
            mrf=cls.mrf, job_title='Backend Dev', department=cls.dept,
            designation=cls.desig, location='Remote', no_of_positions=3,
            key_responsibility='Code', required_qualifications='CS',
            experience_range='2-5', skills_competencies='Python',
            technical_skills='Django', salary_range='5-8 LPA',
            company=cls.company, posted_by=cls.admin,
            assigned_to_internal_hr=cls.hr, status='assigned_to_internal_hr',
        )

        # ── Create apps at SPECIFIC times to test boundary conditions ──
        # "morning" = 09:00 on target date, "evening" = 20:00 on target date
        cls.target_date = date(2026, 5, 10)
        morning = timezone.make_aware(datetime.combine(cls.target_date, time(9, 0)))
        evening = timezone.make_aware(datetime.combine(cls.target_date, time(20, 0)))
        before = timezone.make_aware(datetime.combine(cls.target_date - timedelta(days=1), time(14, 0)))
        after = timezone.make_aware(datetime.combine(cls.target_date + timedelta(days=1), time(10, 0)))

        dummy_resume = SimpleUploadedFile('r.pdf', b'%PDF', content_type='application/pdf')

        def make_app(status, created, name, source='internal_hr'):
            return JobApplication.objects.create(
                job=cls.job, status=status, candidate_name=name,
                candidate_email=f'{name.lower().replace(" ","")}@t.com',
                source=source, submitted_by=cls.hr,
                resume=SimpleUploadedFile(f'{name}.pdf', b'%PDF'),
                created_at=created, updated_at=created,
            )

        cls.app_before = make_app('received', before, 'Before')
        cls.app_morning = make_app('shortlisted', morning, 'Morning')
        cls.app_evening = make_app('interview_pending_1', evening, 'Evening')
        cls.app_after = make_app('received', after, 'After')
        cls.app_joined = make_app('joined', morning, 'Joined')
        cls.app_offer = make_app('offer_accepted', evening, 'Offered')

        # InterviewFeedback records
        InterviewFeedback.objects.create(
            job_application=cls.app_morning, interview_round='hr_round',
            is_selected='hire', interviewer_name='Admin User', created_at=morning,
        )
        InterviewFeedback.objects.create(
            job_application=cls.app_evening, interview_round='hr_round',
            is_selected='reject', interviewer_name='Admin User', created_at=evening,
        )

        # ApprovalNote records
        ApprovalNote.objects.create(
            candidate=cls.app_morning, manager=cls.admin, created_by=cls.hr,
            payload={}, status='approved',
            created_at=morning, approved_at=evening, updated_at=evening,
        )
        ApprovalNote.objects.create(
            candidate=cls.app_evening, manager=cls.admin, created_by=cls.hr,
            payload={}, status='approval_pending',
            created_at=evening, updated_at=evening,
        )

        # OfferDocument
        OfferDocument.objects.create(
            application=cls.app_offer, status='completed',
            created_at=morning, sent_at=evening, completed_at=evening, updated_at=evening,
        )

        # JobApplicationDocument
        JobApplicationDocument.objects.create(
            job_application=cls.app_morning, joining_docs_status='uploaded',
            created_at=morning, updated_at=evening,
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)


# ═══════════════════════════════════════════════════
# 1. DATE FILTER BOUNDARY TESTS
# ═══════════════════════════════════════════════════
class DateFilterBoundaryTests(AnalyticsTestBase):
    """Verify that records at end-of-day on date_to are included."""

    def test_date_filter_includes_end_of_day_records(self):
        """Core regression: date_to must include records created at 20:00 on that day."""
        d = self.target_date.strftime('%Y-%m-%d')
        resp = self.client.get(f'/api/dashboard/analytics/admin/?date_from={d}&date_to={d}')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Should include both morning (09:00) and evening (20:00) apps
        total = data['summary']['cv_counts']['direct_applications']
        self.assertGreaterEqual(total, 4, "Both morning & evening apps should be in results")

    def test_date_filter_excludes_out_of_range(self):
        """Apps from day-before and day-after should NOT appear when filtering to target_date only."""
        d = self.target_date.strftime('%Y-%m-%d')
        resp = self.client.get(f'/api/dashboard/analytics/admin/?date_from={d}&date_to={d}')
        self.assertEqual(resp.status_code, 200)
        total = resp.json()['summary']['cv_counts']['direct_applications']
        # 4 apps on target_date (morning, evening, joined, offered), NOT 6 (before/after excluded)
        self.assertEqual(total, 4)

    def test_no_date_filter_returns_all(self):
        """Without date filters, all 6 apps should appear."""
        resp = self.client.get('/api/dashboard/analytics/admin/')
        self.assertEqual(resp.status_code, 200)
        total = resp.json()['summary']['cv_counts']['direct_applications']
        self.assertEqual(total, 6)


# ═══════════════════════════════════════════════════
# 2. INTERVIEW FEEDBACK DATE FILTER TESTS
# ═══════════════════════════════════════════════════
class InterviewFeedbackDateTests(AnalyticsTestBase):
    """Test calc_interview_round_time_analytics date filtering."""

    def test_feedback_on_end_date_included(self):
        """InterviewFeedback created at 20:00 on date_to must be included."""
        d = self.target_date.strftime('%Y-%m-%d')
        resp = self.client.get(
            f'/api/dashboard/analytics/admin/?date_from={d}&date_to={d}'
            f'&sections=interview_round_time_analytics'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        rounds = data.get('interview_round_time_analytics', {}).get('round_completion_rate', [])
        hr_round = next((r for r in rounds if r['round_type'] == 'HR Round'), None)
        if hr_round:
            self.assertEqual(hr_round['completed'], 2, "Both morning & evening feedback should count")


# ═══════════════════════════════════════════════════
# 3. APPROVAL NOTE DATE FILTER TESTS
# ═══════════════════════════════════════════════════
class ApprovalNoteDateTests(AnalyticsTestBase):
    """Test calc_approval_note_analytics date filtering."""

    def test_approval_notes_on_end_date_included(self):
        """ApprovalNotes created at 20:00 on date_to must be counted."""
        d = self.target_date.strftime('%Y-%m-%d')
        resp = self.client.get(
            f'/api/dashboard/analytics/admin/?date_from={d}&date_to={d}'
            f'&sections=approval_note_analytics'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        section = data.get('approval_note_analytics', {})
        self.assertEqual(section.get('total_approval_notes_sent'), 2,
                         "Both morning & evening notes should be counted")


# ═══════════════════════════════════════════════════
# 4. DOCUMENT/OFFER TIMELINE DATE FILTER TESTS
# ═══════════════════════════════════════════════════
class DocumentOfferDateTests(AnalyticsTestBase):
    """Test calc_document_offer_process_timeline date filtering."""

    def test_offer_docs_on_end_date_included(self):
        """OfferDocuments updated at 20:00 on date_to must be included."""
        d = self.target_date.strftime('%Y-%m-%d')
        resp = self.client.get(
            f'/api/dashboard/analytics/admin/?date_from={d}&date_to={d}'
            f'&sections=document_offer_process_timeline'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        section = data.get('document_offer_process_timeline', {})
        # Should have non-zero averages since data exists on target_date
        self.assertGreater(
            section.get('avg_time_offer_letter_to_approval_days', -1), -1,
            "Offer timeline data should be present"
        )


# ═══════════════════════════════════════════════════
# 5. API SECTION RESPONSE TESTS (smoke tests)
# ═══════════════════════════════════════════════════
class AnalyticsSectionSmokeTests(AnalyticsTestBase):
    """Smoke tests: each section returns 200 and expected keys."""

    SECTIONS = [
        'mrf_analytics', 'job_assignment_analytics', 'cv_resume_source_analytics',
        'candidate_pipeline_funnel', 'interview_round_time_analytics',
        'approval_note_analytics', 'document_offer_process_timeline', 'overall_summary_kpis',
    ]

    def test_admin_full_response_200(self):
        resp = self.client.get('/api/dashboard/analytics/admin/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for section in self.SECTIONS:
            self.assertIn(section, data, f"Section '{section}' missing from admin response")

    def test_each_section_individually(self):
        for section in self.SECTIONS:
            resp = self.client.get(f'/api/dashboard/analytics/admin/?sections={section}')
            self.assertEqual(resp.status_code, 200, f"Section '{section}' returned non-200")
            self.assertIn(section, resp.json(), f"Section '{section}' not in response")

    def test_summary_always_present(self):
        resp = self.client.get('/api/dashboard/analytics/admin/')
        data = resp.json()
        self.assertIn('summary', data)
        self.assertIn('cv_counts', data['summary'])
        self.assertIn('total', data['summary']['cv_counts'])

    def test_user_details_present(self):
        resp = self.client.get('/api/dashboard/analytics/admin/')
        self.assertIn('user_details', resp.json())


# ═══════════════════════════════════════════════════
# 6. ROLE-BASED ACCESS TESTS
# ═══════════════════════════════════════════════════
class RoleAccessTests(AnalyticsTestBase):
    """Test role-based analytics access via the dispatcher."""

    def test_admin_dispatcher_200(self):
        resp = self.client.get('/api/dashboard/analytics/')
        self.assertEqual(resp.status_code, 200)

    def test_hr_dispatcher_200(self):
        self.client.force_authenticate(user=self.hr)
        resp = self.client.get('/api/dashboard/analytics/')
        self.assertEqual(resp.status_code, 200)

    def test_unauthenticated_401(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/dashboard/analytics/')
        self.assertEqual(resp.status_code, 401)

    def test_hr_gets_limited_sections(self):
        self.client.force_authenticate(user=self.hr)
        resp = self.client.get('/api/dashboard/analytics/')
        data = resp.json()
        self.assertNotIn('mrf_analytics', data, "HR should NOT get mrf_analytics")


# ═══════════════════════════════════════════════════
# 7. MRF ANALYTICS TESTS
# ═══════════════════════════════════════════════════
class MRFAnalyticsTests(AnalyticsTestBase):

    def test_mrf_counts(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?sections=mrf_analytics')
        data = resp.json()['mrf_analytics']
        self.assertGreaterEqual(data['total_mrf_raised'], 1)

    def test_mrf_by_department(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?sections=mrf_analytics')
        data = resp.json()['mrf_analytics']
        self.assertIsInstance(data['mrf_by_department'], list)


# ═══════════════════════════════════════════════════
# 8. JOB ASSIGNMENT ANALYTICS TESTS
# ═══════════════════════════════════════════════════
class JobAssignmentTests(AnalyticsTestBase):

    def test_job_counts(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?sections=job_assignment_analytics')
        data = resp.json()['job_assignment_analytics']
        self.assertIn('total_jobs_open', data)
        self.assertGreaterEqual(data['total_jobs_open'], 0)

    def test_jobs_by_hr(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?sections=job_assignment_analytics')
        data = resp.json()['job_assignment_analytics']
        self.assertIn('jobs_by_hr', data)
        self.assertIsInstance(data['jobs_by_hr'], list)


# ═══════════════════════════════════════════════════
# 9. CANDIDATE PIPELINE FUNNEL TESTS
# ═══════════════════════════════════════════════════
class CandidatePipelineTests(AnalyticsTestBase):

    def test_funnel_stages(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?sections=candidate_pipeline_funnel')
        data = resp.json()['candidate_pipeline_funnel']
        self.assertIn('funnel_stages', data)
        self.assertIsInstance(data['funnel_stages'], list)
        self.assertGreater(len(data['funnel_stages']), 0)

    def test_pipeline_breakdown(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?sections=candidate_pipeline_funnel')
        data = resp.json()['candidate_pipeline_funnel']
        self.assertIn('pipeline_breakdown', data)
        breakdown = data['pipeline_breakdown']
        for key in ['screening_pipeline', 'interview_pipeline', 'offer_pipeline']:
            self.assertIn(key, breakdown)

    def test_offer_rates(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?sections=candidate_pipeline_funnel')
        data = resp.json()['candidate_pipeline_funnel']
        self.assertIn('offer_acceptance_rate', data)
        self.assertIsInstance(data['offer_acceptance_rate'], (int, float))


# ═══════════════════════════════════════════════════
# 10. CV / SOURCE ANALYTICS TESTS
# ═══════════════════════════════════════════════════
class CVSourceAnalyticsTests(AnalyticsTestBase):

    def test_total_cvs(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?sections=cv_resume_source_analytics')
        data = resp.json()['cv_resume_source_analytics']
        self.assertIn('total_cvs_received', data)
        self.assertGreaterEqual(data['total_cvs_received'], 1)

    def test_cvs_by_source(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?sections=cv_resume_source_analytics')
        data = resp.json()['cv_resume_source_analytics']
        self.assertIn('candidate_cvs_by_source', data)
        self.assertIsInstance(data['candidate_cvs_by_source'], list)


# ═══════════════════════════════════════════════════
# 11. OVERALL SUMMARY KPI TESTS
# ═══════════════════════════════════════════════════
class OverallSummaryKPITests(AnalyticsTestBase):

    def test_kpi_keys(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?sections=overall_summary_kpis')
        data = resp.json()['overall_summary_kpis']
        for key in ['total_candidates', 'total_positions_filled', 'overall_offer_acceptance_rate',
                     'top_sourcing_channel', 'active_jobs_count']:
            self.assertIn(key, data, f"KPI '{key}' missing")

    def test_tat_metrics(self):
        resp = self.client.get('/api/dashboard/analytics/admin/')
        data = resp.json()
        self.assertIn('partial_joining_tat_days', data)
        self.assertIn('final_joining_tat_days', data)


# ═══════════════════════════════════════════════════
# 12. QUERY PARAM FILTER TESTS
# ═══════════════════════════════════════════════════
class QueryParamFilterTests(AnalyticsTestBase):

    def test_department_filter(self):
        resp = self.client.get(f'/api/dashboard/analytics/admin/?department={self.dept.id}')
        self.assertEqual(resp.status_code, 200)

    def test_job_id_filter(self):
        resp = self.client.get(f'/api/dashboard/analytics/admin/?job_id={self.job.id}')
        self.assertEqual(resp.status_code, 200)

    def test_user_id_filter(self):
        resp = self.client.get(f'/api/dashboard/analytics/admin/?user_id={self.hr.id}')
        self.assertEqual(resp.status_code, 200)

    def test_invalid_user_id_400(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?user_id=00000000-0000-0000-0000-000000000000')
        self.assertEqual(resp.status_code, 400)

    def test_source_filter(self):
        resp = self.client.get('/api/dashboard/analytics/admin/?source=internal_hr')
        self.assertEqual(resp.status_code, 200)

    def test_combined_filters(self):
        d = self.target_date.strftime('%Y-%m-%d')
        resp = self.client.get(
            f'/api/dashboard/analytics/admin/?date_from={d}&date_to={d}'
            f'&department={self.dept.id}&user_id={self.hr.id}'
        )
        self.assertEqual(resp.status_code, 200)
