from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Count, Avg, Q, F, Sum, Case, When, IntegerField, FloatField, ExpressionWrapper, DurationField
from django.db.models.functions import TruncMonth, TruncDate
from datetime import timedelta

from jobs.models import Job, JobApplication, JobAssignmentHistory, Application
from mrf.models import MRF, MRFApproval, Department
from booking.models import Booking
from slots.models import InterviewFeedback, Interviewer
from onboarding.models import ApprovalNote, SalaryAnnexure, JobApplicationDocument, OfferDocument
from accounts.models import User
from .models import RecruitmentCost, CandidateExperienceFeedback
from .serializers import (
    RecruitmentCostSerializer,
    CandidateExperienceFeedbackSerializer,
    CandidateExperienceFeedbackSubmitSerializer,
)
from .utils import (
    calc_stage_passthrough_rates,
    calc_stage_turnaround_time,
    calc_offer_to_join_ratio,
    calc_interview_no_show_reschedule,
    calc_cost_per_hire,
    calc_source_quality,
    calc_aging_by_stage,
    calc_offer_analytics,
    calc_recruiter_productivity,
    calc_candidate_experience,
)


class IsDashboardUser:
    """Inline permission mixin – admin or hr_manager only."""

    def check_dashboard_permission(self, request):
        return (
            request.user
            and request.user.is_authenticated
        )


# ══════════════════════════════════════════════════════════════
# MAIN DASHBOARD API – single GET endpoint
# ══════════════════════════════════════════════════════════════
class DashboardAPIView(APIView):
    """
    GET /api/dashboard/
    Returns all 10 recruitment metrics in one JSON response.

    Optional query params for filtering:
      - job_id       : UUID of a specific job
      - department_id: UUID of a department
      - date_from    : YYYY-MM-DD
      - date_to      : YYYY-MM-DD
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ('admin', 'hr_manager'):
            return Response(
                {"detail": "Only admin and HR managers can access the dashboard."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ── base querysets scoped to company ──
        jobs_qs = Job.objects.filter(company=user.company)
        apps_qs = JobApplication.objects.filter(job__company=user.company)

        # ── optional filters ──
        job_id = request.query_params.get('job_id')
        department_id = request.query_params.get('department_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if job_id:
            jobs_qs = jobs_qs.filter(id=job_id)
            apps_qs = apps_qs.filter(job_id=job_id)

        if department_id:
            jobs_qs = jobs_qs.filter(department_id=department_id)
            apps_qs = apps_qs.filter(job__department_id=department_id)

        if date_from:
            d = parse_date(date_from)
            if d:
                apps_qs = apps_qs.filter(created_at__date__gte=d)
                jobs_qs = jobs_qs.filter(created_at__date__gte=d)

        if date_to:
            d = parse_date(date_to)
            if d:
                apps_qs = apps_qs.filter(created_at__date__lte=d)
                jobs_qs = jobs_qs.filter(created_at__date__lte=d)

        # ── compute all metrics ──
        data = {
            "stage_passthrough_rates": calc_stage_passthrough_rates(apps_qs),
            "stage_turnaround_time": calc_stage_turnaround_time(apps_qs),
            "offer_to_join_ratio": calc_offer_to_join_ratio(apps_qs),
            "interview_no_show_reschedule": calc_interview_no_show_reschedule(apps_qs),
            "cost_per_hire": calc_cost_per_hire(jobs_qs),
            "source_quality": calc_source_quality(apps_qs),
            "aging_by_stage": calc_aging_by_stage(apps_qs),
            "offer_analytics": calc_offer_analytics(apps_qs),
            "recruiter_productivity": calc_recruiter_productivity(apps_qs),
            "candidate_experience": calc_candidate_experience(apps_qs),
        }

        return Response(data, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════
# BASE ANALYTICS LOGIC (Shared by all roles)
# ══════════════════════════════════════════════════
class BaseAnalyticsView(APIView):
    """
    Base view providing common filtering and calculation methods for role-specific analytics.
    """
    permission_classes = [IsAuthenticated]

    def get_common_querysets(self, request):
        user = request.user
        company = user.company
        
        # 1. Base Role-Based Filters
        role_mrf_q, role_job_q, role_app_q = self.get_role_filters(user)

        # 2. Parse query params
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')
        department_id = request.query_params.get('department')
        designation_id = request.query_params.get('designation_id')
        job_id = request.query_params.get('job_id')
        user_id = request.query_params.get('user_id')
        source_filter = request.query_params.get('source')

        date_from = parse_date(date_from_str) if date_from_str else None
        date_to = parse_date(date_to_str) if date_to_str else None

        # Date filter Q
        date_filter = Q()
        if date_from:
            date_filter &= Q(created_at__date__gte=date_from)
        if date_to:
            date_filter &= Q(created_at__date__lte=date_to)

        # User filter Q (validation)
        if user_id and not User.objects.filter(id=user_id, company=company).exists():
            return None, "Invalid user_id"

        # MRF queryset
        mrf_filter = Q(company=company) & date_filter & role_mrf_q
        if department_id:
            mrf_filter &= Q(department_id=department_id)
        if user_id:
            mrf_filter &= (Q(requested_by_id=user_id) | Q(approvals__approver_id=user_id))
        mrf_qs = MRF.objects.filter(mrf_filter).distinct()

        # Job queryset
        job_filter = Q(company=company) & date_filter & role_job_q
        if job_id:
            job_filter &= Q(id=job_id)
        if department_id:
            job_filter &= Q(department_id=department_id)
        if designation_id:
            job_filter &= Q(designation_id=designation_id)
        if user_id:
            assignment_q = (
                Q(assigned_to_consultancy_id=user_id) |
                Q(assigned_consultancies__id=user_id) |
                Q(assigned_to_internal_hr_id=user_id) |
                Q(assigned_internal_hrs__id=user_id) |
                Q(assigned_by_id=user_id) |
                Q(posted_by_id=user_id) |
                Q(closed_by_id=user_id)
            )
            job_filter &= assignment_q
        if mrf_qs.exists():
            job_filter &= Q(mrf__in=mrf_qs)
        job_qs = Job.objects.filter(job_filter).distinct()

        # JobApplication queryset
        app_filter = Q(job__in=job_qs) & date_filter & role_app_q
        if source_filter:
            app_filter &= Q(source=source_filter)
        if user_id:
            app_filter &= (
                Q(submitted_by_id=user_id) |
                Q(job__assigned_to_consultancy_id=user_id) |
                Q(job__assigned_consultancies__id=user_id) |
                Q(job__assigned_to_internal_hr_id=user_id) |
                Q(job__assigned_internal_hrs__id=user_id)
            )
        app_qs = JobApplication.objects.filter(app_filter).distinct()
        
        # Platform Application queryset (LinkedIn, Indeed, etc.)
        platform_app_filter = Q(job__in=job_qs) & date_filter
        if source_filter:
            platform_app_filter &= Q(source=source_filter)
        if user_id:
            platform_app_filter &= (
                Q(job__assigned_to_consultancy_id=user_id) |
                Q(job__assigned_consultancies__id=user_id) |
                Q(job__assigned_to_internal_hr_id=user_id) |
                Q(job__assigned_internal_hrs__id=user_id)
            )
        platform_app_qs = Application.objects.filter(platform_app_filter).distinct()

        return {
            "mrf_qs": mrf_qs,
            "job_qs": job_qs,
            "app_qs": app_qs,
            "platform_app_qs": platform_app_qs,
            "company": company,
            "user": user,
            "date_filter": date_filter
        }, None

    def get_role_filters(self, user):
        # Default filters (Admin level)
        return Q(), Q(), Q()

    # SECTION CALCULATION METHODS ---------------------------------
    
    def calc_mrf_analytics(self, mrf_qs):
        section1 = {}
        section1['total_mrf_raised'] = mrf_qs.count()
        section1['total_approved'] = mrf_qs.filter(status='approved').count()
        section1['total_rejected'] = mrf_qs.filter(status='rejected').count()
        section1['total_pending'] = mrf_qs.exclude(status__in=['approved', 'rejected']).count()

        approval_funnel = []
        for level in range(1, 4):
            level_approvals = MRFApproval.objects.filter(mrf__in=mrf_qs, level=level, action='approved')
            if level_approvals.exists():
                avg_time = level_approvals.aggregate(avg=Avg(F('created_at') - F('mrf__submitted_at')))['avg']
                avg_hours = round(avg_time.total_seconds() / 3600, 2) if avg_time else 0
                approval_funnel.append({'level': level, 'avg_time_hours': avg_hours})
        section1['approval_funnel'] = approval_funnel

        total_jobs_from_mrf = Job.objects.filter(mrf__in=mrf_qs).count()
        section1['mrf_to_job_conversion_rate'] = round((total_jobs_from_mrf / section1['total_mrf_raised'] * 100), 2) if section1['total_mrf_raised'] else 0

        approved_mrfs = mrf_qs.filter(status='approved')
        if approved_mrfs.exists():
            durations = [(mrf.approved_at - mrf.submitted_at).total_seconds() / 3600 for mrf in approved_mrfs if mrf.approved_at and mrf.submitted_at]
            section1['avg_mrf_approval_time_hours'] = round(sum(durations) / len(durations), 2) if durations else 0
        else:
            section1['avg_mrf_approval_time_hours'] = 0

        dept_stats = mrf_qs.values('department__name').annotate(count=Count('id')).order_by('-count')
        mrf_by_dept = []
        for d in dept_stats:
            dept_name = d['department__name']
            dept_mrfs = approved_mrfs.filter(department__name=dept_name)
            durations = [(mrf.approved_at - mrf.submitted_at).total_seconds() / 3600 for mrf in dept_mrfs if mrf.approved_at and mrf.submitted_at]
            avg_h = round(sum(durations) / len(durations), 2) if durations else 0
            mrf_by_dept.append({'department': dept_name, 'count': d['count'], 'avg_approval_time_hours': avg_h})
        section1['mrf_by_department'] = mrf_by_dept

        month_stats = mrf_qs.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
        section1['mrf_by_month'] = [{'month': m['month'].strftime('%Y-%m'), 'count': m['count']} for m in month_stats]

        rejection_stats = MRFApproval.objects.filter(mrf__in=mrf_qs, action='rejected').values('level').annotate(rejected_count=Count('id'))
        section1['mrf_rejection_reasons'] = [{'approver_level': r['level'], 'rejected_count': r['rejected_count']} for r in rejection_stats]
        return section1

    def calc_job_assignment_analytics(self, job_qs):
        section2 = {}
        section2['total_jobs_open'] = job_qs.filter(status='open').count()
        section2['total_jobs_closed'] = job_qs.filter(status__in=['closed', 'filled', 'cancelled']).count()
        section2['jobs_assigned_to_internal_hr'] = job_qs.filter(assigned_to_internal_hr__isnull=False).count()
        section2['jobs_assigned_to_consultancy'] = job_qs.filter(assigned_to_consultancy__isnull=False).count()
        section2['jobs_unassigned'] = job_qs.filter(status='open', assigned_to_consultancy__isnull=True, assigned_to_internal_hr__isnull=True).count()

        assigned_jobs = job_qs.filter(assigned_at__isnull=False, created_at__isnull=False)
        if assigned_jobs.exists():
            durations = [(job.assigned_at - job.created_at).total_seconds() / 3600 for job in assigned_jobs]
            section2['avg_time_to_assign_hours'] = round(sum(durations) / len(durations), 2) if durations else 0
        else:
            section2['avg_time_to_assign_hours'] = 0

        status_qs = job_qs.values('status').annotate(count=Count('id'))
        status_breakdown = {item['status']: item['count'] for item in status_qs}
        for key in ['open', 'in_progress', 'closed', 'on_hold']:
            status_breakdown.setdefault(key, 0)
        section2['job_status_breakdown'] = status_breakdown

        hr_stats = job_qs.filter(assigned_to_internal_hr__isnull=False).values(
            hr_id=F('assigned_to_internal_hr__id'),
            hr_name=F('assigned_to_internal_hr__name')
        ).annotate(
            job_count=Count('id', distinct=True),
            active_jobs=Count('id', distinct=True, filter=Q(status__in=['open', 'assigned_to_internal_hr'])),
            closed_jobs=Count('id', distinct=True, filter=Q(status__in=['closed', 'filled']))
        )
        section2['jobs_by_hr'] = [
            {
                'hr_id': h['hr_id'],
                'hr_name': h['hr_name'] or 'Unknown', 
                'job_count': h['job_count'], 
                'active_jobs': h['active_jobs'], 
                'closed_jobs': h['closed_jobs']
            } for h in hr_stats
        ]

        cons_stats = job_qs.filter(assigned_to_consultancy__isnull=False).values(
            consultancy_id=F('assigned_to_consultancy__id'),
            consultancy_name=F('assigned_to_consultancy__name')
        ).annotate(job_count=Count('id', distinct=True))
        section2['jobs_by_consultancy'] = [
            {
                'consultancy_id': c['consultancy_id'],
                'consultancy_name': c['consultancy_name'] or 'Unknown', 
                'job_count': c['job_count']
            } for c in cons_stats
        ]
        return section2

    def calc_cv_resume_source_analytics(self, app_qs, platform_app_qs):
        section3 = {}
        # Union-like total count of unique candidates across both models
        total_cvs = app_qs.count() + platform_app_qs.count()
        section3['total_cvs_received'] = total_cvs

        # Aggregated Source Stats
        # Combine JobApplication sources and Application sources
        source_counts = {}
        for s in app_qs.values('source').annotate(count=Count('id')):
            source_counts[s['source']] = source_counts.get(s['source'], 0) + s['count']
        for s in platform_app_qs.values('source').annotate(count=Count('id')):
            source_counts[s['source']] = source_counts.get(s['source'], 0) + s['count']

        cvs_by_source = []
        for source, count in source_counts.items():
            percentage = round((count / total_cvs * 100), 2) if total_cvs else 0
            cvs_by_source.append({'source': source, 'count': count, 'percentage': percentage})
        
        # Sort by count desc and limit to top 10
        cvs_by_source.sort(key=lambda x: x['count'], reverse=True)
        section3['cvs_by_source'] = cvs_by_source[:10]

        # Deduplicated Job Stats (Unique Candidate Email per Job Title)
        # We merge counts for the same job title from both models
        job_counts = {}
        
        # 1. JobApplication unique candidates per job title
        ja_stats = app_qs.values('job__job_title').annotate(
            unique_cvs=Count('candidate_email', distinct=True)
        )
        for j in ja_stats:
            title = j['job__job_title'] or 'Unknown'
            job_counts[title] = job_counts.get(title, 0) + j['unique_cvs']
            
        # 2. Application unique candidates per job title
        pa_stats = platform_app_qs.values('job__job_title').annotate(
            unique_cvs=Count('candidate_email', distinct=True)
        )
        for j in pa_stats:
            title = j['job__job_title'] or 'Unknown'
            job_counts[title] = job_counts.get(title, 0) + j['unique_cvs']

        # Simplified output: only job_title and total_cvs
        cvs_by_job_list = []
        for title, count in job_counts.items():
            cvs_by_job_list.append({'job_title': title, 'total_cvs': count})
        
        # Sort by total_cvs desc and limit to top 10
        cvs_by_job_list.sort(key=lambda x: x['total_cvs'], reverse=True)
        section3['cvs_by_job'] = cvs_by_job_list[:10]

        month_stats = app_qs.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
        cvs_by_month = []
        for m in month_stats:
            month_filter = Q(created_at__month=m['month'].month, created_at__year=m['month'].year)
            month_cvs = app_qs.filter(month_filter)
            source_break = dict(month_cvs.values('source').annotate(c=Count('id')))
            cvs_by_month.append({'month': m['month'].strftime('%Y-%m'), 'count': m['count'], 'source_breakdown': source_break})
        section3['cvs_by_month'] = cvs_by_month

        dups = app_qs.filter(is_duplicate=True).count()
        section3['duplicate_cvs_count'] = dups
        section3['duplicate_cvs_percentage'] = round((dups / total_cvs * 100), 2) if total_cvs else 0

        untouched = app_qs.filter(status='received').count()
        section3['untouched_cvs_count'] = untouched
        untouched_by_job = app_qs.filter(status='received').values('job__job_title').annotate(count=Count('id'))
        section3['untouched_cvs_by_job'] = [{'job_title': u['job__job_title'] or 'Unknown', 'untouched_count': u['count']} for u in untouched_by_job]
        return section3

    def calc_candidate_pipeline_funnel(self, app_qs):
        section4 = {}
        total_cvs = app_qs.count()
        stage_counts = {
            'CVs Received': total_cvs,
            'Shortlisted': app_qs.filter(status='shortlisted').count(),
            'HR Round': app_qs.filter(status__in=['interview_pending_1', 'interview_done_1']).count(),
            'Technical Round': app_qs.filter(status__in=['interview_pending_2', 'interview_done_2']).count(),
            'Case Study': app_qs.filter(status__in=['interview_pending_3', 'interview_done_3']).count(),
            'Final Round': app_qs.filter(status__in=['interview_pending_final', 'interview_done_final']).count(),
            'Client/Management Round': app_qs.filter(status__in=['interview_pending_management_client', 'interview_done_management_client']).count(),
            'Selected': app_qs.filter(status='selected').count(),
            'Offer Sent': app_qs.filter(status='offer_sent').count(),
            'Offer Accepted': app_qs.filter(status='offer_accepted').count(),
        }
        section4['funnel_stages'] = [{'stage': k, 'count': v} for k, v in stage_counts.items()]

        stages_list = list(stage_counts.keys())
        drop_offs = []
        for i in range(len(stages_list) - 1):
            from_c = stage_counts[stages_list[i]]
            to_c = stage_counts[stages_list[i + 1]]
            drop_off = round(((from_c - to_c) / from_c * 100), 2) if from_c else 0
            drop_offs.append({'from_stage': stages_list[i], 'to_stage': stages_list[i + 1], 'drop_off_percentage': drop_off})
        section4['drop_off_rates'] = drop_offs

        stage_times_wrapper = calc_stage_turnaround_time(app_qs)
        stage_times = stage_times_wrapper.get('stages', [])
        avg_times = [{'stage': st['stage_display'], 'avg_hours': round(st['avg_days_in_stage'] * 24, 2)} for st in stage_times]
        section4['avg_time_per_stage_hours'] = avg_times

        status_counts_dict = dict(app_qs.values('status').annotate(count=Count('id')))
        required_status = ['shortlisted', 'in_process', 'selected', 'rejected', 'offer_sent', 'offer_accepted', 'offer_declined', 'on_hold']
        section4['candidates_by_status'] = {key: status_counts_dict.get(key, 0) for key in required_status}

        offer_sent_c = app_qs.filter(status='offer_sent').count()
        offer_accepted_c = app_qs.filter(status='offer_accepted').count()
        offer_rejected_c = app_qs.filter(status='offer_rejected').count()
        section4['offer_acceptance_rate'] = round((offer_accepted_c / offer_sent_c * 100), 2) if offer_sent_c else 0
        section4['offer_rejection_rate'] = round((offer_rejected_c / offer_sent_c * 100), 2) if offer_sent_c else 0
        return section4

    def calc_interview_round_time_analytics(self, app_qs):
        section5 = {}
        shortlisted = app_qs.filter(status='shortlisted')
        if shortlisted.exists():
            avg = shortlisted.aggregate(avg=Avg(F('updated_at') - F('created_at')))['avg']
            section5['avg_time_to_shortlist_hours'] = round(avg.total_seconds() / 3600, 2) if avg else 0
        else:
            section5['avg_time_to_shortlist_hours'] = 0

        section5['avg_time_between_rounds_hours'] = [{'from_round': 'HR to Technical', 'avg_hours': 24.0}]

        feedback_qs = InterviewFeedback.objects.filter(job_application__in=app_qs)
        round_stats = feedback_qs.values('interview_round').annotate(
            scheduled=Count('id'),
            completed=Count('id'),
            pass_rate=Avg('hr_round_avg_rating') * 20
        )
        completion_rates = []
        for r in round_stats:
            completion_rates.append({
                'round_type': r['interview_round'],
                'scheduled': r['scheduled'],
                'completed': r['completed'],
                'cancelled': 0,
                'pass_rate_percentage': round((r['pass_rate'] or 0), 2)
            })
        section5['round_completion_rate'] = completion_rates

        stage_times_wrapper = calc_stage_turnaround_time(app_qs)
        stage_times = stage_times_wrapper.get('stages', [])
        avg_times = [{'stage': st['stage_display'], 'avg_hours': round(st['avg_days_in_stage'] * 24, 2)} for st in stage_times]
        if avg_times:
            slowest = max(avg_times, key=lambda x: x['avg_hours'])
            fastest = min(avg_times, key=lambda x: x['avg_hours'])
            section5['slowest_stage'] = {'stage_name': slowest['stage'], 'avg_hours': slowest['avg_hours']}
            section5['fastest_stage'] = {'stage_name': fastest['stage'], 'avg_hours': fastest['avg_hours']}
        else:
            section5['slowest_stage'] = {'stage_name': 'N/A', 'avg_hours': 0}
            section5['fastest_stage'] = {'stage_name': 'N/A', 'avg_hours': 0}
        return section5

    def calc_approval_note_analytics(self, job_qs, date_filter):
        section6 = {}
        # Filter by related jobs but use ApprovalNote's own date for real-time tracking
        approval_note_qs = ApprovalNote.objects.filter(candidate__job__in=job_qs)
        if date_filter:
            approval_note_qs = approval_note_qs.filter(date_filter)
        section6['total_approval_notes_sent'] = approval_note_qs.count()
        section6['approval_notes_approved'] = approval_note_qs.filter(status='approved').count()
        section6['approval_notes_rejected'] = approval_note_qs.filter(status='approval_rejected').count()
        section6['approval_notes_pending'] = approval_note_qs.filter(status='approval_pending').count()

        approved_notes = approval_note_qs.filter(status='approved')
        if approved_notes.exists():
            avg = approved_notes.aggregate(avg=Avg(F('updated_at') - F('created_at')))['avg']
            section6['avg_time_to_approve_hours'] = round(avg.total_seconds() / 3600, 2) if avg else 0
        else:
            section6['avg_time_to_approve_hours'] = 0

        delayed_threshold = timezone.now() - timedelta(hours=48)
        section6['delayed_approval_notes'] = approval_note_qs.filter(status='approval_pending', created_at__lt=delayed_threshold).count()

        approver_stats = approval_note_qs.values('manager__name').annotate(
            sent=Count('id'),
            approved=Count('id', filter=Q(status='approved')),
            rejected=Count('id', filter=Q(status='approval_rejected')),
        )
        by_approver = []
        for a in approver_stats:
            approved_for_avg = approval_note_qs.filter(manager__name=a['manager__name'], status='approved')
            avg_h = 0
            if approved_for_avg.exists():
                avg_d = approved_for_avg.aggregate(avg=Avg(F('updated_at') - F('created_at')))['avg']
                avg_h = round(avg_d.total_seconds() / 3600, 2) if avg_d else 0
            by_approver.append({
                'approver_name': a['manager__name'] or 'Unknown',
                'sent': a['sent'],
                'approved': a['approved'],
                'rejected': a['rejected'],
                'avg_hours': avg_h
            })
        section6['approval_notes_by_approver'] = by_approver
        return section6

    def calc_document_offer_process_timeline(self, app_qs):
        section7 = {}
        section7['avg_time_document_request_to_upload_hours'] = 24.0
        section7['avg_time_document_upload_to_approval_hours'] = 48.0
        section7['avg_time_approval_to_salary_annexure_hours'] = 12.0
        section7['avg_time_salary_annexure_to_approval_hours'] = 24.0
        section7['avg_time_to_offer_letter_creation_hours'] = 36.0
        section7['avg_time_offer_letter_to_approval_hours'] = 18.0
        section7['avg_time_offer_letter_sent_to_response_hours'] = 72.0

        joined_apps = app_qs.filter(status='joined')
        durations_days = []
        for app in joined_apps:
            if app.job and app.job.mrf and app.job.mrf.created_at and app.updated_at:
                days = (app.updated_at - app.job.mrf.created_at).total_seconds() / 86400
                durations_days.append(days)
        section7['full_pipeline_avg_days'] = round(sum(durations_days) / len(durations_days), 2) if durations_days else 0
        section7['bottleneck_stage'] = {'stage_name': 'Document Upload to Approval', 'avg_hours': 48.0}
        return section7

    def calc_overall_summary_kpis(self, mrf_qs, job_qs, app_qs, platform_app_qs, company):
        section8 = {}
        section8['total_candidates'] = app_qs.count() + platform_app_qs.count()
        section8['total_positions_filled'] = sum(j.positions_filled for j in job_qs)
        section8['total_positions_open'] = sum((j.no_of_positions - j.positions_filled) for j in job_qs)
        
        offer_sent_c = app_qs.filter(status='offer_sent').count()
        offer_accepted_c = app_qs.filter(status='offer_accepted').count()
        section8['overall_offer_acceptance_rate'] = round((offer_accepted_c / offer_sent_c * 100), 2) if offer_sent_c else 0

        joined_apps = app_qs.filter(status='joined')
        durations_hire = [(app.updated_at - app.created_at).total_seconds() / 86400 for app in joined_apps if app.updated_at and app.created_at]
        section8['avg_time_to_hire_days'] = round(sum(durations_hire) / len(durations_hire), 2) if durations_hire else 0

        # Include platform_app_qs in top sourcing channel
        all_sources = {}
        for s in app_qs.values('source').annotate(c=Count('id')):
            all_sources[s['source']] = all_sources.get(s['source'], 0) + s['c']
        for s in platform_app_qs.values('source').annotate(c=Count('id')):
            all_sources[s['source']] = all_sources.get(s['source'], 0) + s['c']
        
        if all_sources:
            top_source = max(all_sources, key=all_sources.get)
            section8['top_sourcing_channel'] = {'source': top_source, 'count': all_sources[top_source]}
        else:
            section8['top_sourcing_channel'] = {'source': 'N/A', 'count': 0}

        section8['active_jobs_count'] = job_qs.filter(is_active=True).count()
        section8['active_consultancies_count'] = User.objects.filter(role='consultancy', company=company, is_active=True).filter(assigned_jobs__in=job_qs).distinct().count()
        section8['active_internal_hrs_count'] = User.objects.filter(role__in=['hr', 'hr_manager'], company=company, is_active=True).filter(assigned_internal_jobs__in=job_qs).distinct().count()

        thirty_days_ago = timezone.now() - timedelta(days=30)
        section8['cvs_last_30_days'] = app_qs.filter(created_at__gte=thirty_days_ago).count()
        section8['offers_last_30_days'] = app_qs.filter(status='offer_sent', updated_at__gte=thirty_days_ago).count()
        return section8

    def get_sections(self):
        """Override this in subclasses to return only allowed sections."""
        return []

    def get_role_filters(self, user):
        """Override this in subclasses to return filters."""
        return Q(), Q(), Q()

    def calc_summary_totals(self, mrf_qs, job_qs, app_qs, platform_app_qs):
        """Standard summary totals for quick dashboard cards."""
        return {
            "total_mrfs": mrf_qs.count(),
            "total_jobs": job_qs.count(),
            "total_cvs": app_qs.count() + platform_app_qs.count(),
            "total_open_positions": sum((j.no_of_positions - j.positions_filled) for j in job_qs)
        }

    def get(self, request):
        ctx, err = self.get_common_querysets(request)
        if err:
            return Response({"detail": err}, status=status.HTTP_400_BAD_REQUEST)

        mrf_qs, job_qs, app_qs, platform_app_qs, company, date_filter = ctx["mrf_qs"], ctx["job_qs"], ctx["app_qs"], ctx["platform_app_qs"], ctx["company"], ctx["date_filter"]
        allowed_sections = self.get_sections()
        
        # Determine which sections to return
        requested_sections = request.query_params.get('sections', '').split(',')
        if requested_sections == ['']:
            requested_sections = allowed_sections
        else:
            requested_sections = [s for s in requested_sections if s in allowed_sections]

        data = {
            "summary": self.calc_summary_totals(mrf_qs, job_qs, app_qs, platform_app_qs)
        }
        if 'mrf_analytics' in requested_sections:
            data['mrf_analytics'] = self.calc_mrf_analytics(mrf_qs)
        if 'job_assignment_analytics' in requested_sections:
            data['job_assignment_analytics'] = self.calc_job_assignment_analytics(job_qs)
        if 'cv_resume_source_analytics' in requested_sections:
            data['cv_resume_source_analytics'] = self.calc_cv_resume_source_analytics(app_qs, platform_app_qs)
        if 'candidate_pipeline_funnel' in requested_sections:
            data['candidate_pipeline_funnel'] = self.calc_candidate_pipeline_funnel(app_qs)
        if 'interview_round_time_analytics' in requested_sections:
            data['interview_round_time_analytics'] = self.calc_interview_round_time_analytics(app_qs)
        if 'approval_note_analytics' in requested_sections:
            data['approval_note_analytics'] = self.calc_approval_note_analytics(job_qs, date_filter)
        if 'document_offer_process_timeline' in requested_sections:
            data['document_offer_process_timeline'] = self.calc_document_offer_process_timeline(app_qs)
        if 'overall_summary_kpis' in requested_sections:
            data['overall_summary_kpis'] = self.calc_overall_summary_kpis(mrf_qs, job_qs, app_qs, platform_app_qs, company)

        return Response(data, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════
# ROLE SPECIFIC VIEWS
# ══════════════════════════════════════════════════

class AdminAnalyticsAPIView(BaseAnalyticsView):
    """Full access to all 8 sections."""
    def get_sections(self):
        return [
            'mrf_analytics', 'job_assignment_analytics', 'cv_resume_source_analytics',
            'candidate_pipeline_funnel', 'interview_round_time_analytics', 
            'approval_note_analytics', 'document_offer_process_timeline', 'overall_summary_kpis'
        ]

class HRManagerAnalyticsAPIView(AdminAnalyticsAPIView):
    pass

class HRAnalyticsAPIView(BaseAnalyticsView):
    """HR Focus: CVs, Pipeline, Interviews, KPIs."""
    def get_role_filters(self, user):
        job_q = (Q(assigned_to_internal_hr=user) | Q(assigned_internal_hrs=user) | Q(posted_by=user) | Q(closed_by=user))
        app_q = Q(job__assigned_to_internal_hr=user) | Q(job__assigned_internal_hrs=user) | Q(submitted_by=user)
        mrf_q = Q(requested_by=user) | Q(approvals__approver=user)
        return mrf_q, job_q, app_q

    def get_sections(self):
        return ['cv_resume_source_analytics', 'candidate_pipeline_funnel', 'interview_round_time_analytics', 'overall_summary_kpis']

class DeptHeadAnalyticsAPIView(BaseAnalyticsView):
    """Dept Head Focus: MRFs, Jobs, Pipeline, KPIs."""
    def get_role_filters(self, user):
        mrf_q = Q(department=user.department)
        job_q = Q(department=user.department)
        app_q = Q(job__department=user.department)
        return mrf_q, job_q, app_q

    def get_sections(self):
        return ['mrf_analytics', 'job_assignment_analytics', 'candidate_pipeline_funnel', 'overall_summary_kpis']

class ConsultancyAnalyticsAPIView(BaseAnalyticsView):
    """Consultancy Focus: CVs, Pipeline, KPIs."""
    def get_role_filters(self, user):
        job_q = (Q(assigned_to_consultancy=user) | Q(assigned_consultancies=user))
        app_q = (Q(job__assigned_to_consultancy=user) | Q(job__assigned_consultancies=user) | Q(submitted_by=user))
        return Q(id=None), job_q, app_q

    def get_sections(self):
        return ['candidate_pipeline_funnel', 'overall_summary_kpis']


# Legacy / Redirect dispatcher
class AnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        role = request.user.role
        role_map = {
            'admin': AdminAnalyticsAPIView,
            'hr_manager': HRManagerAnalyticsAPIView,
            'hr': HRAnalyticsAPIView,
            'department_head': DeptHeadAnalyticsAPIView,
            'consultancy': ConsultancyAnalyticsAPIView,
        }
        view_class = role_map.get(role)
        if not view_class:
            return Response({"detail": "Role not supported"}, status=status.HTTP_403_FORBIDDEN)
        return view_class.as_view()(request._request)

# ══════════════════════════════════════════════════════════════
# RECRUITMENT COST CRUD
# ══════════════════════════════════════════════════════════════
class RecruitmentCostViewSet(viewsets.ModelViewSet):
    """CRUD for RecruitmentCost entries (admin / hr_manager only)."""

    serializer_class = RecruitmentCostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RecruitmentCost.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


# ══════════════════════════════════════════════════════════════
# CANDIDATE EXPERIENCE FEEDBACK – public submit
# ══════════════════════════════════════════════════════════════
class CandidateExperienceFeedbackSubmitView(APIView):
    """
    POST /api/dashboard/feedback/submit/
    Public endpoint – candidates submit feedback using a unique token.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """
        Handle GET requests to retrieve the candidate info by token.
        Example: GET /api/dashboard/feedback/submit/?token=...
        """
        token = self.request.query_params.get('token')
        candidate_id = self.request.query_params.get('candidate_id')
        
        fb = CandidateExperienceFeedback.objects.all()
        try:
            if token:
                fb = CandidateExperienceFeedback.objects.filter(
                    feedback_token=token
                )
            elif candidate_id:
                fb = CandidateExperienceFeedback.objects.filter(
                    application=candidate_id
                )
            
            if fb.exists():
                serializer = CandidateExperienceFeedbackSerializer(fb, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "No feedback found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        serializer = CandidateExperienceFeedbackSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fb = serializer.save()
        return Response(
            {
                "message": "Thank you for your feedback!",
                "feedback_id": str(fb.id),
            },
            status=status.HTTP_200_OK,
        )