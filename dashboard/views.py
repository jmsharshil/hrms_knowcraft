from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.utils.dateparse import parse_date
from dateutil import parser
from django.utils import timezone
from django.db.models import Count, Avg, Q, F, Sum, Case, When, IntegerField, FloatField, ExpressionWrapper, DurationField, OuterRef, Subquery
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models.functions import TruncMonth, TruncDate
from datetime import timedelta
from collections import defaultdict
import statistics

from jobs.models import Job, JobApplication, JobAssignmentHistory, Application, ReferralApplication
from mrf.models import MRF, MRFApproval, Department, Designation
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
    calc_joining_tat
)

from accounts.serializers import UserSerializer

# def safe_parse_date(date_str):
#     """
#     Parses a date string into a date object.
#     Prefers Django's strict ISO parser (YYYY-MM-DD) to avoid dayfirst
#     ambiguity for single-digit day/month values (e.g. 2026-03-01).
#     Falls back to dateutil for non-ISO formats.
#     """
#     if not date_str:
#         return None
#     # Try strict ISO format first (handles single-digit days/months correctly)
#     from django.utils.dateparse import parse_date as django_parse_date
#     result = django_parse_date(date_str)
#     if result is not None:
#         return result
#     # Fallback: try dateutil for other formats (DD/MM/YYYY, etc.)
#     try:
#         return parser.parse(date_str, dayfirst=True).date()
#     except (ValueError, TypeError, OverflowError):
#         return None

def safe_parse_date(date_str):
    """
    Parses a date string into a date object.
    Handles single-digit months/days like 2026-5-1 correctly.
    """
    if not date_str:
        return None
    try:
        from datetime import datetime
        # Normalize by splitting and zero-padding each part
        parts = date_str.strip().replace('/', '-').split('-')
        if len(parts) == 3:
            if len(parts[0]) == 4:
                # Format: YYYY-M-D or YYYY-MM-DD
                normalized = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
            else:
                # Format: D-M-YYYY or DD-MM-YYYY
                normalized = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            return datetime.strptime(normalized, "%Y-%m-%d").date()
        # fallback for any other format
        return parser.parse(date_str, dayfirst=True).date()
    except (ValueError, TypeError, OverflowError):
        return None

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
      - user_id      : UUID of a recruiter/consultancy for performance
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

        # ── base querysets scoped to company (Excluding Private Records from General Reports) ──
        jobs_qs = Job.objects.filter(company=user.company, is_private=False)
        apps_qs = JobApplication.objects.filter(job__company=user.company, job__is_private=False)

        # ── optional filters ──
        user_id = request.query_params.get('user_id')
        job_id = request.query_params.get('job_id')
        department_id = request.query_params.get('department_id')
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')
        date_from = safe_parse_date(date_from_str)
        date_to = safe_parse_date(date_to_str)

        target_user = None
        if user_id:
            try:
                target_user = User.objects.get(id=user_id, company=user.company)
            except User.DoesNotExist:
                return Response({"detail": "Invalid user_id"}, status=status.HTTP_400_BAD_REQUEST)

        if job_id:
            jobs_qs = jobs_qs.filter(id=job_id)
            apps_qs = apps_qs.filter(job_id=job_id)

        if department_id:
            jobs_qs = jobs_qs.filter(department_id=department_id)
            apps_qs = apps_qs.filter(job__department_id=department_id)

        from datetime import datetime, time
        from django.utils import timezone
        
        if date_from:
            dt_from = timezone.make_aware(datetime.combine(date_from, time.min))
            apps_qs = apps_qs.filter(created_at__gte=dt_from)
            jobs_qs = jobs_qs.filter(created_at__gte=dt_from)

        if date_to:
            dt_to = timezone.make_aware(datetime.combine(date_to, time.max))
            apps_qs = apps_qs.filter(created_at__lte=dt_to)
            jobs_qs = jobs_qs.filter(created_at__lte=dt_to)

        if user_id:
            if target_user.role == 'consultancy':
                assignment_q = Q(assigned_to_consultancy_id=user_id) | Q(assigned_consultancies__id=user_id)
                jobs_qs = jobs_qs.filter(assignment_q)
                apps_qs = apps_qs.filter(Q(submitted_by_id=user_id) | Q(job__assigned_to_consultancy_id=user_id) | Q(job__assigned_consultancies__id=user_id))
            elif target_user.role in ['hr', 'hr_manager']:
                jobs_qs = jobs_qs.filter(Q(assigned_to_internal_hr_id=user_id) | Q(assigned_internal_hrs__id=user_id) | Q(posted_by_id=user_id))
                apps_qs = apps_qs.filter(Q(submitted_by_id=user_id) | Q(job__assigned_to_internal_hr_id=user_id) | Q(job__assigned_internal_hrs__id=user_id))
            else:
                assignment_q = (
                    Q(assigned_to_consultancy_id=user_id) |
                    Q(assigned_consultancies__id=user_id) |
                    Q(assigned_to_internal_hr_id=user_id) |
                    Q(assigned_internal_hrs__id=user_id) |
                    Q(assigned_by_id=user_id) |
                    Q(posted_by_id=user_id) |
                    Q(closed_by_id=user_id)
                )
                jobs_qs = jobs_qs.filter(assignment_q)
                apps_qs = apps_qs.filter(
                    Q(submitted_by_id=user_id) |
                    Q(job__assigned_to_consultancy_id=user_id) |
                    Q(job__assigned_consultancies__id=user_id) |
                    Q(job__assigned_to_internal_hr_id=user_id) |
                    Q(job__assigned_internal_hrs__id=user_id)
                )

        # ── referral querysets ──
        referral_filter = Q()
        from datetime import datetime, time
        from django.utils import timezone
        if date_from:
            dt_from = timezone.make_aware(datetime.combine(date_from, time.min))
            referral_filter &= Q(created_at__gte=dt_from)
        if date_to:
            dt_to = timezone.make_aware(datetime.combine(date_to, time.max))
            referral_filter &= Q(created_at__lte=dt_to)
        
        if department_id:
            try:
                dept_name = Department.objects.get(id=department_id).name
                referral_filter &= Q(referral_department=dept_name)
            except (Department.DoesNotExist, ValidationError, ValueError):
                referral_filter &= Q(referral_department=department_id)
        
        if user_id:
            referral_filter &= Q(referral_emp_code=user_id)
            
        referral_qs = ReferralApplication.objects.filter(referral_filter).distinct()

        # ── compute all metrics ──
        data = {
            "user_details": UserSerializer(target_user).data if target_user else UserSerializer(user).data,
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
            "referral_stats": {
                "total": referral_qs.count(),
                "by_department": [
                    {"department": r['referral_department'] or 'Unknown', "count": r['count']}
                    for r in referral_qs.values('referral_department').annotate(count=Count('id')).order_by('-count')
                ]
            },
            "approval_note_stats": {
                "total": ApprovalNote.objects.filter(candidate__in=apps_qs).count(),
                "by_status": [
                    {
                        "status": item['status'],
                        "status_display": dict(ApprovalNote.STATUS_CHOICES).get(item['status'], item['status']),
                        "count": item['count']
                    }
                    for item in ApprovalNote.objects.filter(candidate__in=apps_qs).values('status').annotate(count=Count('id')).order_by('-count')
                ]
            },
            "salary_annexure_stats": {
                "total": SalaryAnnexure.objects.filter(job_application__in=apps_qs).count(),
                "by_status": [
                    {
                        "status": item['status'],
                        "status_display": dict(SalaryAnnexure.STATUS_CHOICES).get(item['status'], item['status']),
                        "count": item['count']
                    }
                    for item in SalaryAnnexure.objects.filter(job_application__in=apps_qs).values('status').annotate(count=Count('id')).order_by('-count')
                ]
            }
        }

        assigned_jobs_list = []
        if user_id:
            # Annotate with application count
            annotated_jobs = jobs_qs.annotate(
                number_of_applications=Count('jobapplication')  # Adjust relation name if needed (e.g., 'applications')
            ).order_by('-created_at')[:50]  # Recent first, limit 50

            for job in annotated_jobs:
                assigned_jobs_list.append({
                    'id': job.id,
                    'job_title': job.job_title or 'Unknown',
                    'department_name': getattr(job.department, 'name', None) or 'Unknown',  # Assumes department.name
                    'status': job.status or 'Unknown',
                    'created_at': job.created_at.isoformat() if job.created_at else None,
                    'number_of_applications': job.number_of_applications,
                    'assigned_to': target_user.role,  # Simple role indicator; enhance if needed (e.g., full user details)
                    # Optional: Add more like 'posted_by_id', 'closed_at', etc.
                })
            data["assigned_jobs"] = assigned_jobs_list

        # Special case for recruiter productivity when filtering by specific user (consultancy/hr)
        if target_user and target_user.role in ('consultancy', 'hr', 'hr_manager'):
            now = timezone.now()
            week_start = now - timedelta(days=now.weekday())
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            total_cvs = apps_qs.count()
            cvs_this_week = apps_qs.filter(created_at__gte=week_start).count()

            interview_statuses = [
                'interview_pending_1', 'interview_done_1',
                'interview_pending_2', 'interview_done_2',
                'interview_pending_3', 'interview_done_3',
                'interview_pending_final', 'interview_done_final',
                'interview_pending_management_client', 'interview_done_management_client',
            ]
            interviews_this_week = apps_qs.filter(
                created_at__gte=week_start,
                status__in=interview_statuses
            ).count()

            offer_statuses = ['offer_sent', 'offer_accepted', 'offer_rejected']
            offers_this_month = apps_qs.filter(
                created_at__gte=month_start,
                status__in=offer_statuses
            ).count()

            data["recruiter_productivity"] = {
                "recruiters": [{
                    "recruiter_id": str(target_user.id),
                    "recruiter_name": target_user.name or "N/A",
                    "recruiter_email": target_user.email or "N/A",
                    "total_cvs": total_cvs,
                    "cvs_this_week": cvs_this_week,
                    "interviews_this_week": interviews_this_week,
                    "offers_this_month": offers_this_month,
                }]
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
        designation_id = request.query_params.get('designation')
        job_id = request.query_params.get('job_id')
        user_id = request.query_params.get('user_id')
        source_filter = request.query_params.get('source')

        date_from = safe_parse_date(date_from_str)
        date_to = safe_parse_date(date_to_str)

        # Date filter Q — use timezone-aware datetime boundaries to correctly
        # capture records on the exact date_from / date_to days.
        from datetime import datetime, time
        from django.utils import timezone
        date_filter = Q()
        if date_from:
            dt_from = timezone.make_aware(datetime.combine(date_from, time.min))
            date_filter &= Q(created_at__gte=dt_from)
        if date_to:
            dt_to = timezone.make_aware(datetime.combine(date_to, time.max))
            date_filter &= Q(created_at__lte=dt_to)

        # User filter Q (validation)
        target_user = None
        if user_id:
            try:
                target_user = User.objects.get(id=user_id, company=company)
            except User.DoesNotExist:
                return None, "Invalid user_id"

        # 3. MRF queryset (Filtered by Period Activity)
        mrf_base_filter = Q(company=company, is_private=False) & role_mrf_q
        if department_id:
            mrf_base_filter &= Q(department_id=department_id)
        if designation_id:
            mrf_base_filter &= Q(designation_id=designation_id)
        if user_id:
            mrf_base_filter &= (Q(requested_by_id=user_id) | Q(approvals__approver_id=user_id))
        
        mrf_qs = MRF.objects.filter(mrf_base_filter & date_filter).distinct()

        # 4. Job queryset
        # Base filter includes company, role, dept, desig, and user but NO date
        job_base_filter = Q(company=company, is_private=False) & role_job_q
        if job_id:
            job_base_filter &= Q(id=job_id)
        if department_id:
            job_base_filter &= Q(department_id=department_id)
        if designation_id:
            job_base_filter &= Q(designation_id=designation_id)
        if user_id:
            if target_user.role == 'consultancy':
                job_base_filter &= (Q(assigned_to_consultancy_id=user_id) | Q(assigned_consultancies__id=user_id))
            elif target_user.role in ['hr', 'hr_manager']:
                job_base_filter &= (Q(assigned_to_internal_hr_id=user_id) | Q(assigned_internal_hrs__id=user_id) | Q(posted_by_id=user_id))
            else:
                assignment_q = (
                    Q(assigned_to_consultancy_id=user_id) |
                    Q(assigned_consultancies__id=user_id) |
                    Q(assigned_to_internal_hr_id=user_id) |
                    Q(assigned_internal_hrs__id=user_id) |
                    Q(assigned_by_id=user_id) |
                    Q(posted_by_id=user_id) |
                    Q(closed_by_id=user_id)
                )
                job_base_filter &= assignment_q
        
        # broad_job_qs: Used for activity tracking (apps, notes) across all relevant jobs
        broad_job_qs = Job.objects.filter(job_base_filter).distinct()
        
        # job_qs: Used for "Job Analytics" (new jobs created in period)
        job_period_filter = job_base_filter & date_filter
        # Conditional MRF link: keep logic but use the broad base for jobs
        # unless you specifically only want jobs for THIS month's MRFs.
        # Fixed: Jobs are shown if created in period, regardless of MRF date.
        job_qs = Job.objects.filter(job_period_filter).distinct()

        # 5. JobApplication queryset (Filtered by Period Activity)
        app_filter = Q(job__in=broad_job_qs) & date_filter & role_app_q
        if source_filter:
            app_filter &= Q(source=source_filter)
        if user_id:
            if target_user.role == 'consultancy':
                app_filter &= Q(submitted_by_id=user_id) | Q(application_link__created_by_id=user_id)
            elif target_user.role in ['hr', 'hr_manager', 'admin']:
                app_filter &= (Q(submitted_by_id=user_id) | Q(job__assigned_to_internal_hr_id=user_id) | Q(job__assigned_internal_hrs__id=user_id) | Q(job__posted_by_id=user_id) | Q(job__closed_by_id=user_id))
            else:
                 app_filter &= (
                    Q(submitted_by_id=user_id) |
                    Q(job__assigned_to_consultancy_id=user_id) |
                    Q(job__assigned_consultancies__id=user_id) |
                    Q(job__assigned_to_internal_hr_id=user_id) |
                    Q(job__assigned_internal_hrs__id=user_id) |
                    Q(job__posted_by_id=user_id) |
                    Q(job__closed_by_id=user_id) |
                    Q(job__mrf__requested_by_id=user_id)
                )
        app_qs = JobApplication.objects.filter(app_filter).distinct()
        
        # 6. Platform Application queryset (LinkedIn, Indeed, etc.)
        job_titles = list(broad_job_qs.values_list('job_title', flat=True))
        platform_job_q = Q(job__in=broad_job_qs)
        platform_orphan_q = Q(job__isnull=True, position_title__in=job_titles)
        platform_app_filter = (platform_job_q | platform_orphan_q) & date_filter
        
        if source_filter:
            platform_app_filter &= Q(source=source_filter)
        if user_id:
            if target_user.role == 'consultancy':
                platform_app_qs = Application.objects.none()
            else:
                if target_user.role in ['hr', 'hr_manager', 'admin']:
                    access_q = (Q(job__assigned_to_internal_hr_id=user_id) | Q(job__assigned_internal_hrs__id=user_id) | Q(job__posted_by_id=user_id) | Q(job__closed_by_id=user_id))
                else:
                    access_q = (
                        Q(job__assigned_to_consultancy_id=user_id) |
                        Q(job__assigned_consultancies__id=user_id) |
                        Q(job__assigned_to_internal_hr_id=user_id) |
                        Q(job__assigned_internal_hrs__id=user_id) |
                        Q(job__posted_by_id=user_id) |
                        Q(job__closed_by_id=user_id)
                    )
                # Allow orphans that matched name, or jobs the user has access to
                platform_app_filter &= (access_q | platform_orphan_q)
                platform_app_qs = Application.objects.filter(platform_app_filter).distinct()
        else:
            platform_app_qs = Application.objects.filter(platform_app_filter).distinct()

        referral_filter = date_filter
        if department_id:
            try:
                # ReferralApplication stores department as a string name, resolve UUID if possible
                dept_name = Department.objects.get(id=department_id).name
                referral_filter &= Q(referral_department=dept_name)
            except (Department.DoesNotExist, ValidationError, ValueError):
                # referral_filter &= Q(referral_department=department_id)
                pass

        if designation_id:
            try:
                # ReferralApplication stores designation as a string name, resolve UUID if possible
                desig_name = Designation.objects.get(id=designation_id).name
                referral_filter &= Q(referral_designation=desig_name)
            except (Designation.DoesNotExist, ValidationError, ValueError):
                # referral_filter &= Q(referral_designation=designation_id)
                pass

        if user_id:
            user_email = User.objects.get(id=user_id).email
            referral_filter &= Q(referral_email=user_email)

        referral_qs = ReferralApplication.objects.filter(referral_filter).distinct()

        return {
            "mrf_qs": mrf_qs,
            "job_qs": job_qs,
            "broad_job_qs": broad_job_qs,
            "app_qs": app_qs,
            "platform_app_qs": platform_app_qs,
            "referral_qs": referral_qs,
            "company": company,
            "user": user,
            "target_user": target_user,
            "date_filter": date_filter,
            "date_from": date_from,
            "date_to": date_to
        }, None

    def get_role_filters(self, user):
        # Default filters (Admin level)
        return Q(), Q(), Q()

    # SECTION CALCULATION METHODS ---------------------------------
    
    def calc_mrf_analytics(self, mrf_qs):
        section1 = {}
        section1['total_mrf_raised'] = mrf_qs.count()
        section1['total_approved'] = mrf_qs.filter(status__in=['approved', 'filled', 'joining_pending']).count()
        section1['total_rejected'] = mrf_qs.filter(status='rejected').count()
        section1['total_on_hold'] = mrf_qs.filter(status='on_hold').count()
        section1['total_pending'] = mrf_qs.exclude(status__in=['approved', 'filled', 'joining_pending', 'rejected', 'on_hold']).count()

        # Calculate transition time between levels:
        # Level 1: mrf.submitted_at to level 1 approval
        # Level 2: level 1 approval to level 2 approval
        # Level 3: level 2 approval to level 3 approval
        approvals = MRFApproval.objects.filter(
            mrf__in=mrf_qs,
            action='approved'
        ).values('mrf_id', 'level', 'created_at', 'mrf__submitted_at')

        mrf_approval_times = defaultdict(dict)
        mrf_submitted_at = {}
        for app in approvals:
            mrf_id = app['mrf_id']
            level = app['level']
            mrf_approval_times[mrf_id][level] = app['created_at']
            if app['mrf__submitted_at']:
                mrf_submitted_at[mrf_id] = app['mrf__submitted_at']

        level_durations = defaultdict(list)
        for mrf_id, times in mrf_approval_times.items():
            submitted = mrf_submitted_at.get(mrf_id)
            if not submitted:
                continue
            
            # Level 1: submitted_at -> level 1
            if 1 in times:
                dur = (times[1] - submitted).total_seconds()
                if dur >= 0:
                    level_durations[1].append(dur)
            
            # Level 2: level 1 -> level 2 (fallback to submitted_at if level 1 is missing)
            if 2 in times:
                start = times.get(1, submitted)
                dur = (times[2] - start).total_seconds()
                if dur >= 0:
                    level_durations[2].append(dur)
                
            # Level 3: level 2 -> level 3 (fallback to level 1, then submitted_at)
            if 3 in times:
                start = times.get(2, times.get(1, submitted))
                dur = (times[3] - start).total_seconds()
                if dur >= 0:
                    level_durations[3].append(dur)

        approval_funnel = []
        for level in range(1, 4):
            durations = level_durations.get(level, [])
            if durations:
                avg_seconds = sum(durations) / len(durations)
                avg_days = round(avg_seconds / 86400, 2)
            else:
                avg_days = 0
            approval_funnel.append({'level': level, 'avg_time_days': avg_days})
        section1['approval_funnel'] = approval_funnel

        total_jobs_from_mrf = Job.objects.filter(mrf__in=mrf_qs).count()
        section1['mrf_to_job_conversion_rate'] = round((total_jobs_from_mrf / section1['total_mrf_raised'] * 100), 2) if section1['total_mrf_raised'] else 0

        approved_mrfs = mrf_qs.filter(status__in=['approved', 'filled', 'joining_pending'])
        if approved_mrfs.exists():
            durations = []
            for mrf in approved_mrfs:
                if mrf.approved_at and mrf.submitted_at:
                    td = (mrf.approved_at - mrf.submitted_at).total_seconds() / 86400
                    if td >= 0:
                        durations.append(td)
            section1['avg_mrf_approval_time_days'] = round(sum(durations) / len(durations), 2) if durations else 0
        else:
            section1['avg_mrf_approval_time_days'] = 0

        dept_stats = mrf_qs.values('department__name').annotate(count=Count('id')).order_by('-count')
        mrf_by_dept = []
        for d in dept_stats:
            dept_name = d['department__name']
            dept_mrfs = approved_mrfs.filter(department__name=dept_name)
            durations = []
            for mrf in dept_mrfs:
                if mrf.approved_at and mrf.submitted_at:
                    td = (mrf.approved_at - mrf.submitted_at).total_seconds() / 86400
                    if td >= 0:
                        durations.append(td)
            avg_days = round(sum(durations) / len(durations), 2) if durations else 0
            mrf_by_dept.append({'department': dept_name, 'count': d['count'], 'avg_approval_time_days': avg_days})
        section1['mrf_by_department'] = mrf_by_dept

        month_stats = mrf_qs.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
        section1['mrf_by_month'] = [{'month': m['month'].strftime('%Y-%m'), 'count': m['count']} for m in month_stats]

        # Summary of rejections per level
        rejection_summary = MRFApproval.objects.filter(mrf__in=mrf_qs, action='rejected').values('level').annotate(count=Count('id')).order_by('level')
        section1['mrf_rejection_summary'] = [{'level': r['level'], 'total_rejected': r['count']} for r in rejection_summary]

        # Detailed rejection reasons by level
        rejections = MRFApproval.objects.filter(mrf__in=mrf_qs, action='rejected').select_related('mrf', 'approver').values(
            'level', 'rejection_reason', 'mrf__mrf_name', 'created_at', 'approver__name'
        ).order_by('-created_at')
        
        section1['mrf_rejection_reasons'] = [
            {
                'approver_level': r['level'],
                'mrf_name': r['mrf__mrf_name'],
                'rejected_by': r['approver__name'] or 'System/Unknown',
                'reason': r['rejection_reason'] or 'No reason provided',
                'date': r['created_at'].strftime('%Y-%m-%d %H:%M') if r['created_at'] else 'N/A'
            }
            for r in rejections
        ]
        return section1

    def calc_job_assignment_analytics(self, job_qs, user_role=None, target_user_id=None):
        section2 = {}
        section2['total_jobs_open'] = job_qs.filter(status__in=['open','assigned_to_internal_hr','assigned_to_consultancy','assigned_to_both']).count()
        section2['total_jobs_closed'] = job_qs.filter(status__in=['filled', 'joining_pending']).count()
        section2['total_jobs_on_hold'] = job_qs.filter(status='on_hold').count()
        section2['jobs_assigned_to_internal_hr'] = job_qs.filter(Q(status='assigned_to_internal_hr') | Q(previous_status='assigned_to_internal_hr') | Q(status='assigned_to_both') | Q(previous_status='assigned_to_both')).count()
        section2['jobs_assigned_to_consultancy'] = job_qs.filter(Q(status='assigned_to_consultancy') | Q(previous_status='assigned_to_consultancy') | Q(status='assigned_to_both') | Q(previous_status='assigned_to_both')).count()
        section2['jobs_assigned_to_both'] = job_qs.filter(Q(status='assigned_to_both') | Q(previous_status='assigned_to_both')).count()
        section2['jobs_unassigned'] = job_qs.filter(status='open').count()

        assigned_jobs = job_qs.filter(assigned_at__isnull=False, created_at__isnull=False)
        durations = []
        for job in assigned_jobs:
            td = (job.assigned_at - job.created_at).total_seconds() / 86400
            if td >= 0:
                durations.append(td)
        section2['avg_time_to_assign_days'] = round(sum(durations) / len(durations), 2) if durations else 0

        status_qs = job_qs.values('status').annotate(count=Count('id'))
        status_breakdown = {item['status']: item['count'] for item in status_qs}
        for key in ['open', 'closed', 'on_hold']:
            status_breakdown.setdefault(key, 0)
        section2['job_status_breakdown'] = status_breakdown

        hr_dict = {}
        cons_dict = {}

        # Efficiently fetch all assigned jobs with necessary relations
        jobs_with_details = job_qs.select_related(
            'assigned_to_internal_hr', 
            'assigned_to_consultancy', 
            'department'
        ).prefetch_related(
            'assigned_internal_hrs', 
            'assigned_consultancies'
        )

        for job in jobs_with_details:
            # 1. Process HRs (Both primary and M2M)
            hrs = []
            if job.assigned_to_internal_hr:
                hrs.append(job.assigned_to_internal_hr)
            for m2m_hr in job.assigned_internal_hrs.all():
                if job.assigned_to_internal_hr and m2m_hr.id == job.assigned_to_internal_hr.id:
                    continue
                hrs.append(m2m_hr)
            
            job_detail = {
                'id': str(job.id),
                'job_title': job.job_title,
                'status': job.status,
                'department_name': job.department.name if job.department else 'N/A',
                'no_of_positions': job.no_of_positions,
                'positions_filled': job.positions_filled,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'assignment_date': (job.assigned_at or job.assigned_internal_at).isoformat() if (job.assigned_at or job.assigned_internal_at) else None
            }

            for hr in hrs:
                hid = str(hr.id)
                if target_user_id and hid != str(target_user_id):
                    continue

                if hid not in hr_dict:
                    hr_dict[hid] = {
                        'hr_id': hid,
                        'hr_name': hr.name or hr.email or 'Unknown',
                        'job_count': 0,
                        'active_jobs': 0,
                        'closed_jobs': 0,
                        'on_hold_jobs': 0,
                        'jobs': []
                    }
                
                hr_dict[hid]['job_count'] += 1
                if job.status in ['filled', 'joining_pending']:
                    hr_dict[hid]['closed_jobs'] += 1
                elif job.status == 'on_hold':
                    hr_dict[hid]['on_hold_jobs'] += 1
                elif job.status not in ['closed', 'cancelled']:
                    hr_dict[hid]['active_jobs'] += 1
                hr_dict[hid]['jobs'].append(job_detail)

            # 2. Process Consultancies (Both primary and M2M)
            conss = []
            if job.assigned_to_consultancy:
                conss.append(job.assigned_to_consultancy)
            for m2m_cons in job.assigned_consultancies.all():
                if job.assigned_to_consultancy and m2m_cons.id == job.assigned_to_consultancy.id:
                    continue
                conss.append(m2m_cons)
            
            for cons in conss:
                cid = str(cons.id)
                if target_user_id and cid != str(target_user_id):
                    continue

                if cid not in cons_dict:
                    cons_dict[cid] = {
                        'consultancy_id': cid,
                        'consultancy_name': cons.name or cons.email or 'Unknown',
                        'job_count': 0,
                        'active_jobs': 0,
                        'closed_jobs': 0,
                        'on_hold_jobs': 0,
                        'jobs': []
                    }
                
                cons_dict[cid]['job_count'] += 1
                if job.status in ['filled', 'joining_pending']:
                    cons_dict[cid]['closed_jobs'] += 1
                elif job.status == 'on_hold':
                    cons_dict[cid]['on_hold_jobs'] += 1
                elif job.status not in ['closed', 'cancelled']:
                    cons_dict[cid]['active_jobs'] += 1
                cons_dict[cid]['jobs'].append(job_detail)

        if user_role != 'consultancy':
            section2['jobs_by_hr'] = sorted(list(hr_dict.values()), key=lambda x: x['hr_name'])
        section2['jobs_by_consultancy'] = sorted(list(cons_dict.values()), key=lambda x: x['consultancy_name'])
        
        return section2

    def calc_cv_resume_source_analytics(self, app_qs, platform_app_qs, referral_qs, total_interviews_override=None):
        section3 = {}
        # Union-like total count across both models
        ja_count = app_qs.count()
        pa_count = platform_app_qs.filter(is_touched=False).count()
        referral_count = referral_qs.filter(is_touched=False).count()
        total_cvs = ja_count + pa_count + referral_count
        section3['total_cvs_received'] = total_cvs

        source_display_map = {
            'internal_hr': 'Internal HR',
            'consultancy': 'Consultancy',
            'application_link': 'Application Link',
            'referral': 'Referral',
            'direct': 'Direct',
            'career_page': 'Career Page',
            'linkedin': 'LinkedIn',
            'indeed': 'Indeed',
            'naukri': 'Naukri',
        }

        def normalize_source_name(src):
            if not src:
                return 'Unknown'
            src_lower = src.lower()
            return source_display_map.get(src_lower) or src.replace('_', ' ').title()

        # Aggregated Source Stats
        # Combine JobApplication sources and Application sources
        source_counts = {}
        for s in app_qs.values('source').annotate(count=Count('id')):
            src = normalize_source_name(s['source'])
            source_counts[src] = source_counts.get(src, 0) + s['count']

        cvs_by_source = []
        for source, count in source_counts.items():
            percentage = round((count / ja_count * 100), 2) if ja_count else 0
            cvs_by_source.append({'source': source, 'count': count, 'percentage': percentage})
        
        # Sort by count desc and limit to top 10
        cvs_by_source.sort(key=lambda x: x['count'], reverse=True)
        section3['candidate_cvs_by_source'] = cvs_by_source[:10]

        # Platform Sources Stats
        platform_source_counts = {}
        for s in platform_app_qs.values('source').annotate(count=Count('id')):
            src = normalize_source_name(s['source'])
            platform_source_counts[src] = platform_source_counts.get(src, 0) + s['count']

        platform_cvs_by_source = []
        for source, count in platform_source_counts.items():
            percentage = round((count / pa_count * 100), 2) if pa_count else 0
            platform_cvs_by_source.append({'source': source, 'count': count, 'percentage': percentage})

        platform_cvs_by_source.sort(key=lambda x: x['count'], reverse=True)
        section3['platform_cvs_by_source'] = platform_cvs_by_source[:10]

        # Combined Platform, Candidate, and Referral Sources Stats
        combined_source_counts = {}
        for s in app_qs.values('source').annotate(count=Count('id')):
            src = normalize_source_name(s['source'])
            combined_source_counts[src] = combined_source_counts.get(src, 0) + s['count']
        for s in platform_app_qs.values('source').annotate(count=Count('id')):
            src = normalize_source_name(s['source'])
            combined_source_counts[src] = combined_source_counts.get(src, 0) + s['count']
        
        # Include referrals count with 'Referral' source
        combined_source_counts['Referral'] = combined_source_counts.get('Referral', 0) + referral_count

        combined_cvs_by_source = []
        for source, count in combined_source_counts.items():
            percentage = round((count / total_cvs * 100), 2) if total_cvs else 0
            combined_cvs_by_source.append({'source': source, 'count': count, 'percentage': percentage})

        combined_cvs_by_source.sort(key=lambda x: x['count'], reverse=True)
        section3['combined_cvs_by_source'] = combined_cvs_by_source
        # Deduplicated Job Stats (Unique Candidate Email per Job Title)
        # We merge counts for the same job title from both models
        job_counts = {}
        ja_stats = app_qs.values('job__job_title').annotate(unique_cvs=Count('candidate_email', distinct=True))
        for j in ja_stats:
            title = j['job__job_title'] or 'Unknown'
            job_counts[title] = job_counts.get(title, 0) + j['unique_cvs']
            
        pa_stats = platform_app_qs.values('job__job_title', 'position_title').annotate(unique_cvs=Count('candidate_email', distinct=True))
        for j in pa_stats:
            title = j['job__job_title'] or j.get('position_title') or 'Unknown'
            job_counts[title] = job_counts.get(title, 0) + j['unique_cvs']

        cvs_by_job_list = [{'job_title': title, 'total_cvs': count} for title, count in job_counts.items()]
        cvs_by_job_list.sort(key=lambda x: x['total_cvs'], reverse=True)
        section3['cvs_by_job'] = cvs_by_job_list[:10]

        # Monthly Matrix Breakdown (Combined)
        months_ja = app_qs.annotate(month=TruncMonth('created_at')).values_list('month', flat=True).distinct()
        months_pa = platform_app_qs.annotate(month=TruncMonth('created_at')).values_list('month', flat=True).distinct()
        all_months = sorted(list(set(filter(None, list(months_ja) + list(months_pa)))))

        cvs_by_month = []
        for m_date in all_months:
            m_ja = app_qs.filter(created_at__month=m_date.month, created_at__year=m_date.year)
            m_pa = platform_app_qs.filter(created_at__month=m_date.month, created_at__year=m_date.year)
            
            m_count = m_ja.count() + m_pa.count()
            source_break = {}
            for s in m_ja.values('source').annotate(c=Count('id')):
                source_break[s['source']] = source_break.get(s['source'], 0) + s['c']
            for s in m_pa.values('source').annotate(c=Count('id')):
                source_break[s['source']] = source_break.get(s['source'], 0) + s['c']
                
            cvs_by_month.append({
                'month': m_date.strftime('%Y-%m'),
                'count': m_count,
                'source_breakdown': source_break
            })
        section3['cvs_by_month'] = cvs_by_month

        dups = app_qs.filter(is_duplicate=True).count() + platform_app_qs.filter(is_duplicate=True).count()
        section3['duplicate_cvs_count'] = dups
        section3['duplicate_cvs_percentage'] = round((dups / total_cvs * 100), 2) if total_cvs else 0

        # Combined untouched aggregation from all 3 querysets (Candidate Management, Platform, and Referral)
        untouched_map = defaultdict(lambda: {'count': 0, 'job_ids': set()})

        # 1. Candidate Management (app_qs)
        for u in app_qs.filter(status='received').values(
            'job__designation__name',
            'job__department__name',
            'job__job_title',
            'job__id'
        ):
            desig = u['job__designation__name'] or 'Unknown'
            dept = u['job__department__name'] or 'Unknown'
            title = u['job__job_title'] or 'Unknown'
            key = (desig, dept, title)
            untouched_map[key]['count'] += 1
            if u['job__id']:
                untouched_map[key]['job_ids'].add(u['job__id'])

        # 2. Platform Applications (platform_app_qs)
        for u in platform_app_qs.filter(is_touched=False, is_rejected=False).values(
            'designation__name',
            'department__name',
            'job__job_title',
            'position_title',
            'job__id'
        ):
            desig = u['designation__name'] or 'Unknown'
            dept = u['department__name'] or 'Unknown'
            title = u['job__job_title'] or u['position_title'] or 'Unknown'
            key = (desig, dept, title)
            untouched_map[key]['count'] += 1
            if u['job__id']:
                untouched_map[key]['job_ids'].add(u['job__id'])

        # 3. Referral Applications (referral_qs)
        for u in referral_qs.values(
            'referral_designation',
            'referral_department',
            'position_title'
        ):
            desig = u['referral_designation'] or 'Unknown'
            dept = u['referral_department'] or 'Unknown'
            title = u['position_title'] or 'Unknown'
            key = (desig, dept, title)
            untouched_map[key]['count'] += 1

        # Build list
        untouched_list = []
        for (desig, dept, title), data in untouched_map.items():
            untouched_list.append({
                'designation_name': desig,
                'department_name': dept,
                'untouched_count': data['count'],
                'job_title': title,
                'job_ids': list(data['job_ids']),
            })

        # Sort by count desc
        untouched_list.sort(key=lambda x: x['untouched_count'], reverse=True)
        
        section3['untouched_cvs_count'] = sum(x['untouched_count'] for x in untouched_list)
        section3['untouched_cvs_by_job'] = untouched_list
        section3['interview_no_show_reschedule'] = calc_interview_no_show_reschedule(app_qs, total_interviews_override)

        # Referral by Department breakdown
        referral_dept_stats = referral_qs.values('referral_department').annotate(count=Count('id')).order_by('-count')
        section3['referral_by_department'] = [
            {
                'department': r['referral_department'] or 'Unknown',
                'count': r['count']
            }
            for r in referral_dept_stats
        ]
        return section3

    def calc_candidate_pipeline_funnel(self, app_qs, target_user=None, interviewer_app_ids=None):
        section4 = {}
        
        # If filtering by interviewer, narrow down candidates experience to those they actually touched
        experience_app_qs = app_qs
        if interviewer_app_ids:
            experience_app_qs = app_qs.filter(id__in=interviewer_app_ids)
        total_cvs = app_qs.count()
        # statuses in order of progression
        # Define base lists of subsequent statuses for each stage to ensure cumulative logic is robust
        # Base terminal successes
        joined_st = ['joined']
        joining_pending_st = ['joining_pending', 'joining_poned'] + joined_st
        docs_st = ['docs_pending', 'docs_uploaded', 'review_docs', 'docs_approved', 'docs_incomplete', 'docs_unclear'] + joining_pending_st
        offer_accepted_st = ['offer_accepted'] + docs_st
        offer_sent_st = ['offer_sent', 'offer_rejected'] + offer_accepted_st
        offer_prep_st = ['offer_pending'] + offer_sent_st
        salary_st = ['salary_annexure_prep', 'salary_annexure_review', 'approved_annexure', 'rejected_annexure'] + offer_prep_st
        approved_st = ['approved', 'approval_rejected'] + salary_st
        approval_pending_st = ['approval_pending'] + approved_st
        selected_st = ['selected'] + approval_pending_st
        
        # Management / Client Round
        mgt_promoted_st = ['interview_next_management_client', 'consolidated_result_review'] + selected_st
        mgt_completed_st = ['interview_done_management_client', 'interview_rejected_management_client'] + mgt_promoted_st
        mgt_reached_st = ['interview_pending_management_client'] + mgt_completed_st

        # Final Round
        final_promoted_st = ['interview_next_final'] + mgt_reached_st
        final_completed_st = ['interview_done_final', 'interview_rejected_final'] + final_promoted_st
        final_reached_st = ['interview_pending_final'] + final_completed_st

        # Case Study Round
        case_promoted_st = ['interview_next_3'] + final_reached_st
        case_completed_st = ['interview_done_3', 'interview_rejected_3'] + case_promoted_st
        case_reached_st = ['interview_pending_3'] + case_completed_st

        # Technical Round
        tech_promoted_st = ['interview_next_2'] + case_reached_st
        tech_completed_st = ['interview_done_2', 'interview_rejected_2'] + tech_promoted_st
        tech_reached_st = ['interview_pending_2'] + tech_completed_st

        # HR Round
        hr_promoted_st = tech_reached_st
        hr_completed_st = ['interview_done_1', 'interview_rejected_1'] + hr_promoted_st
        hr_reached_st = ['interview_pending_1'] + hr_completed_st

        # Top of Funnel
        shortlisted_st = ['shortlisted'] + hr_reached_st
        received_st = ['received', 'duplicate_rejected', 'rejected'] + shortlisted_st

        # Build Granular Funnel
        ordered_stages = [
            ('CVs Received', received_st),
            ('Duplicate Rejected', ['duplicate_rejected']),
            ('Shortlisted', shortlisted_st),
            
            ('Reached HR Round', hr_reached_st),
            ('Completed HR Round', hr_completed_st),
            ('Rejected at HR', ['interview_rejected_1']),
            ('Promoted to Tech Round', tech_reached_st),
            
            ('Reached Technical Round', tech_reached_st),
            ('Completed Technical Round', tech_completed_st),
            ('Rejected at Tech', ['interview_rejected_2']),
            ('Promoted to Case Study', case_reached_st),
            
            ('Reached Case Study Round', case_reached_st),
            ('Completed Case Study Round', case_completed_st),
            ('Rejected at Case Study', ['interview_rejected_3']),
            ('Promoted to Final Round', final_reached_st),
            
            ('Reached Final Round', final_reached_st),
            ('Completed Final Round', final_completed_st),
            ('Rejected at Final', ['interview_rejected_final']),
            ('Promoted to Mgt/Client Round', mgt_reached_st),
            
            ('Reached Mgt/Client Round', mgt_reached_st),
            ('Completed Mgt/Client Round', mgt_completed_st),
            ('Rejected at Mgt/Client', ['interview_rejected_management_client']),
            ('Selected', selected_st),
            
            ('Approval Pending', approval_pending_st),
            ('Approved', approved_st),
            ('Offer Sent', offer_sent_st),
            ('Offer Accepted', offer_accepted_st),
            ('Joined', joined_st),
        ]

        stage_counts = {name: app_qs.filter(status__in=statuses).count() for name, statuses in ordered_stages}
        section4['funnel_stages'] = [{'stage': k, 'count': v} for k, v in stage_counts.items()]

        # Define terminal rejection stages to calculate drop-offs correctly without negative percentages
        TERMINAL_REJECTIONS = {
            'Duplicate Rejected', 'Rejected',
            'Rejected at HR', 'Rejected at Tech', 'Rejected at Case Study', 'Rejected at Final', 'Rejected at Mgt/Client',
            'Offer Rejected', 'Approval Rejected', 'Rejected Annexure'
        }

        def get_drop_off_pct(from_stage, to_stage, from_c, to_c):
            if not from_c:
                return 0.0
            if from_stage in TERMINAL_REJECTIONS:
                return 0.0
            if to_stage in TERMINAL_REJECTIONS:
                return max(0.0, round((to_c / from_c * 100), 2))
            return max(0.0, round(((from_c - to_c) / from_c * 100), 2))

        stages_list = [s[0] for s in ordered_stages]
        drop_offs = []
        for i in range(len(stages_list) - 1):
            from_stage = stages_list[i]
            to_stage = stages_list[i + 1]
            if from_stage in TERMINAL_REJECTIONS:
                continue
            from_c = stage_counts[from_stage]
            to_c = stage_counts[to_stage]
            drop_off = get_drop_off_pct(from_stage, to_stage, from_c, to_c)
            drop_offs.append({'from_stage': from_stage, 'to_stage': to_stage, 'drop_off_percentage': drop_off})
        section4['drop_off_rates'] = drop_offs

        stage_times_wrapper = calc_stage_turnaround_time(app_qs)
        stage_times = stage_times_wrapper.get('stages', [])
        avg_times = [{'stage': st['stage_display'], 'avg_days': st['avg_days_in_stage']} for st in stage_times]
        section4['avg_time_per_stage_days'] = avg_times

        status_counts = app_qs.values('status').annotate(count=Count('id'))
        status_counts_dict = {item['status']: item['count'] for item in status_counts}
        
        # Dynamically include all defined statuses from the model
        from jobs.models import JobApplication
        all_defined_statuses = [choice[0] for choice in JobApplication.STATUS_CHOICES]
        section4['candidates_by_status'] = {key: status_counts_dict.get(key, 0) for key in all_defined_statuses}

        offer_sent_statuses = ['offer_sent', 'offer_accepted', 'offer_rejected', 'joined', 'joining_pending', 'joining_poned']
        offer_accepted_statuses = ['offer_accepted', 'joined','joining_pending', 'joining_poned']
        offer_rejected_statuses = ['offer_rejected']
        
        offer_sent_c = app_qs.filter(status__in=offer_sent_statuses).count()
        offer_accepted_c = app_qs.filter(status__in=offer_accepted_statuses).count()
        offer_rejected_c = app_qs.filter(status__in=offer_rejected_statuses).count()
        section4['offer_acceptance_rate'] = round((offer_accepted_c / offer_sent_c * 100), 2) if offer_sent_c else 0
        section4['offer_rejection_rate'] = round((offer_rejected_c / offer_sent_c * 100), 2) if offer_sent_c else 0

        # ── 3 Separate Pipeline Parts ──
        # Helper to build a mini-funnel with stages, drop-offs, and avg turnaround
        def _build_pipeline_part(part_stages, part_app_qs):
            part_counts = {name: part_app_qs.filter(status__in=statuses).count() for name, statuses in part_stages}
            part_funnel = [{'stage': k, 'count': v} for k, v in part_counts.items()]
            part_names = [s[0] for s in part_stages]
            part_drops = []
            for i in range(len(part_names) - 1):
                from_stage = part_names[i]
                to_stage = part_names[i + 1]
                if from_stage in TERMINAL_REJECTIONS:
                    continue
                fc = part_counts[from_stage]
                tc = part_counts[to_stage]
                drop = get_drop_off_pct(from_stage, to_stage, fc, tc)
                part_drops.append({'from_stage': from_stage, 'to_stage': to_stage, 'drop_off_percentage': drop})
            # Avg turnaround: avg days from first stage entry to last stage entry
            part_status_keys = set()
            for _, sts in part_stages:
                part_status_keys.update(sts)
            part_apps_in_scope = part_app_qs.filter(status__in=list(part_status_keys))
            if part_apps_in_scope.exists():
                avg_dur = part_apps_in_scope.aggregate(avg=Avg(F('updated_at') - F('created_at')))['avg']
                avg_days = round(avg_dur.total_seconds() / 86400, 2) if avg_dur else 0
            else:
                avg_days = 0
            return {
                'funnel_stages': part_funnel,
                'drop_off_rates': part_drops,
                'avg_turnaround_days': avg_days
            }

        # Part 1: Screening (Received → Shortlisted only)
        screening_stages = [
            ('CVs Received', received_st),
            ('Shortlisted', shortlisted_st),
        ]

        # Part 2: Interview (HR Round → Selected)
        screening_data = _build_pipeline_part(screening_stages, app_qs)
        interview_stages = [
            ('Reached HR Round', hr_reached_st),
            ('Completed HR Round', hr_completed_st),
            ('Rejected at HR', ['interview_rejected_1']),
            ('Reached Technical Round', tech_reached_st),
            ('Completed Technical Round', tech_completed_st),
            ('Rejected at Tech', ['interview_rejected_2']),
            ('Reached Case Study Round', case_reached_st),
            ('Completed Case Study Round', case_completed_st),
            ('Rejected at Case Study', ['interview_rejected_3']),
            ('Reached Final Round', final_reached_st),
            ('Completed Final Round', final_completed_st),
            ('Rejected at Final', ['interview_rejected_final']),
            ('Reached Mgt/Client Round', mgt_reached_st),
            ('Completed Mgt/Client Round', mgt_completed_st),
            ('Rejected at Mgt/Client', ['interview_rejected_management_client']),
            ('Under HR Review', ['consolidated_result_review'] + selected_st),
            ('Selected', selected_st),
        ]
        interview_data = _build_pipeline_part(interview_stages, app_qs)
        offer_stages = [
            ('Selected', selected_st),
            ('Approval Pending', approval_pending_st),
            ('Approval Rejected', ['approval_rejected']),
            ('Approved', approved_st),
            ('Salary Annexure', salary_st),
            ('Approved Annexure', ['approved_annexure'] + offer_prep_st),
            ('Rejected Annexure', ['rejected_annexure']),
            ('Offer Sent', offer_sent_st),
            ('Offer Rejected', ['offer_rejected']),
            ('Offer Accepted', offer_accepted_st),
            ('Joining Pending', joining_pending_st),
            ('Joined', joined_st),
        ]
        offer_data = _build_pipeline_part(offer_stages, app_qs)

        section4['pipeline_breakdown'] = {
            'screening_pipeline': screening_data,
            'interview_pipeline': interview_data,
            'offer_pipeline': offer_data,
            'pipeline_part_averages': {
                'screening_avg_days': screening_data['avg_turnaround_days'],
                'interview_avg_days': interview_data['avg_turnaround_days'],
                'offer_avg_days': offer_data['avg_turnaround_days'],
            },
        }

        # Candidate experience with total_sent, filled, not_filled counts
        candidate_exp = calc_candidate_experience(experience_app_qs)
        from .models import CandidateExperienceFeedback
        # Feedback is only created on submission, so total_sent = candidates who reached
        # rejection or offer stages AFTER the feature went live.
        # Use earliest feedback record as the cutoff to avoid counting pre-feature candidates.
        feedback_eligible_statuses = [
            'interview_rejected_1', 'interview_rejected_2', 'interview_rejected_3',
            'interview_rejected_final', 'interview_rejected_management_client',
            'offer_accepted', 'offer_rejected',
        ]
        earliest_feedback = CandidateExperienceFeedback.objects.order_by('created_at').values_list('created_at', flat=True).first()
        eligible_qs = experience_app_qs.filter(status__in=feedback_eligible_statuses)
        if earliest_feedback:
            eligible_qs = eligible_qs.filter(updated_at__gte=earliest_feedback)
        else:
            eligible_qs = eligible_qs.none()
        total_sent = eligible_qs.count()
        filled = CandidateExperienceFeedback.objects.filter(
            application__in=experience_app_qs, is_submitted=True
        ).count()
        not_filled = max(total_sent - filled, 0)
        candidate_exp['total_sent'] = total_sent
        candidate_exp['filled'] = filled
        candidate_exp['not_filled'] = not_filled
        section4['candidate_experience'] = candidate_exp

        section4['recruiter_productivity'] = calc_recruiter_productivity(app_qs, target_user.id if target_user else None)
        return section4

    def calc_interview_round_time_analytics(self, app_qs, date_range, company, interviewer_app_ids=None, broad_job_qs=None):
        from collections import defaultdict
        section5 = {}
        date_from, date_to = date_range
        
        # Build a base feedback filter that respects company and role constraints
        # but uses its own date filtering for interviews
        if broad_job_qs is not None:
            feedback_filter = Q(job_application__job__in=broad_job_qs)
        else:
            feedback_filter = Q(job_application__job__company=company)
        
        from datetime import datetime, time
        from django.utils import timezone
        if date_from:
            dt_from = timezone.make_aware(datetime.combine(date_from, time.min))
            feedback_filter &= Q(created_at__gte=dt_from)
        if date_to:
            dt_to = timezone.make_aware(datetime.combine(date_to, time.max))
            feedback_filter &= Q(created_at__lte=dt_to)

        if interviewer_app_ids is not None:
            feedback_filter &= Q(job_application_id__in=interviewer_app_ids)
        
        feedback_qs = InterviewFeedback.objects.filter(feedback_filter)
        
        shortlisted = app_qs.filter(status='shortlisted')
        if shortlisted.exists():
            avg = shortlisted.aggregate(avg=Avg(F('updated_at') - F('created_at')))['avg']
            section5['avg_time_to_shortlist_days'] = round(avg.total_seconds() / 86400, 2) if avg else 0
        else:
            section5['avg_time_to_shortlist_days'] = 0

        # Dynamic average time between rounds
        feedbacks = list(feedback_qs.select_related('job_application').values('job_application_id', 'interview_round', 'created_at'))
        app_feedbacks = defaultdict(list)
        for fb in feedbacks:
            app_feedbacks[fb['job_application_id']].append({
                'round': fb['interview_round'] or 'Unknown',
                'completed_at': fb['created_at']
            })
        between_deltas = defaultdict(list)
        for app_id, fbs in app_feedbacks.items():
            if len(fbs) < 2:
                continue
            # Sort by completed_at
            fbs.sort(key=lambda x: x['completed_at'])
            for i in range(1, len(fbs)):
                prev = fbs[i-1]['round']
                curr = fbs[i]['round']
                delta = (fbs[i]['completed_at'] - fbs[i-1]['completed_at']).total_seconds() / 86400
                if delta >= 0:
                    between_deltas[(prev, curr)].append(delta)

        # Define standard round order with actual DB values
        ordered_rounds = [
            'hr_round', 'technical_round', 'case_study_round',
            'final_round', 'management_client_round'
        ]
        
        round_display = {
            'hr_round': 'HR Round',
            'technical_round': 'Technical Round',
            'case_study_round': 'Case Study Round',
            'final_round': 'Final Round',
            'management_client_round': 'Management / Client Round'
        }

        # ──────────────────────────────────────────────────────────────
        # 16-Stage Turnaround Time (TAT) Progression
        # ──────────────────────────────────────────────────────────────
        from onboarding.models import ApprovalNote, OfferDocument, SalaryAnnexureHistory

        cv_to_short_deltas = []
        short_to_hr_deltas = []
        hr_to_tech_deltas = []
        tech_to_case_deltas = []
        tech_to_final_deltas = []
        case_to_final_deltas = []
        final_to_review_deltas = []
        final_to_mgt_deltas = []
        mgt_to_review_deltas = []
        review_to_selected_deltas = []
        selected_to_note_deltas = []
        note_to_approved_deltas = []
        approved_to_annexure_deltas = []
        annexure_to_approved_annexure_deltas = []
        approved_annexure_to_offer_sent_deltas = []
        offer_sent_to_accepted_or_rejected_deltas = []
        accepted_to_joining_pending_deltas = []
        joining_pending_to_joined_deltas = []

        apps_list = list(app_qs)

        # Build Lookups
        feedbacks = list(feedback_qs.values('job_application_id', 'interview_round', 'created_at'))
        app_feedbacks = defaultdict(list)
        for fb in feedbacks:
            app_feedbacks[fb['job_application_id']].append(fb)

        for app_id in app_feedbacks:
            app_feedbacks[app_id].sort(key=lambda x: x['created_at'])

        approval_notes = list(ApprovalNote.objects.filter(candidate__in=app_qs).values('candidate_id', 'created_at', 'approved_at', 'status'))
        app_notes = {an['candidate_id']: an for an in approval_notes}

        annexure_histories = list(SalaryAnnexureHistory.objects.filter(annexure__job_application__in=app_qs).values('annexure__job_application_id', 'action', 'created_at'))
        app_annexures = defaultdict(list)
        for ah in annexure_histories:
            app_annexures[ah['annexure__job_application_id']].append(ah)

        offers = list(OfferDocument.objects.filter(application__in=app_qs).values('application_id', 'sent_at', 'completed_at', 'signed_at', 'updated_at', 'status'))
        app_offers = defaultdict(list)
        for o in offers:
            app_offers[o['application_id']].append(o)

        post_received_statuses = {
            'shortlisted', 'interview_pending_1', 'interview_done_1', 'interview_rejected_1',
            'interview_next_2', 'interview_pending_2', 'interview_done_2', 'interview_rejected_2',
            'interview_next_3', 'interview_pending_3', 'interview_done_3', 'interview_rejected_3',
            'interview_next_final', 'interview_pending_final', 'interview_done_final', 'interview_rejected_final',
            'interview_next_management_client', 'interview_pending_management_client',
            'interview_done_management_client', 'interview_rejected_management_client',
            'consolidated_result_review', 'selected', 'approval_pending', 'approved', 'approval_rejected',
            'salary_annexure_prep', 'salary_annexure_review', 'approved_annexure', 'rejected_annexure',
            'offer_pending', 'offer_sent', 'offer_accepted', 'offer_rejected',
            'docs_pending', 'docs_uploaded', 'review_docs', 'docs_approved', 'docs_incomplete', 'docs_unclear',
            'joining_pending', 'joining_poned', 'joined'
        }

        # 1. CV Received -> Shortlisted
        for app in apps_list:
            if app.status in post_received_statuses:
                d = (app.updated_at - app.created_at).total_seconds() / 86400
                if d >= 0:
                    cv_to_short_deltas.append(d)

        cv_to_short_days = round(sum(cv_to_short_deltas) / len(cv_to_short_deltas), 2) if cv_to_short_deltas else 0.0

        for app in apps_list:
            app_id = app.id
            created_at = app.created_at
            status = app.status
            updated_at = app.updated_at

            fbs = app_feedbacks.get(app_id, [])
            fb_hr = next((f for f in fbs if f['interview_round'] == 'hr_round'), None)
            fb_tech = next((f for f in fbs if f['interview_round'] == 'technical_round'), None)
            fb_case = next((f for f in fbs if f['interview_round'] == 'case_study_round'), None)
            fb_final = next((f for f in fbs if f['interview_round'] == 'final_round'), None)
            fb_mgt = next((f for f in fbs if f['interview_round'] == 'management_client_round'), None)

            # 2. Shortlisted -> HR Round
            if fb_hr:
                d = (fb_hr['created_at'] - created_at).total_seconds() / 86400
                cv_to_short_time = (updated_at - created_at).total_seconds() / 86400 if status == 'shortlisted' else (cv_to_short_days or 1.0)
                d_short_hr = d - cv_to_short_time
                if d_short_hr < 0:
                    d_short_hr = max(0.1, d / 2)
                short_to_hr_deltas.append(d_short_hr)

            # 3. HR Round -> Technical Round
            if fb_hr and fb_tech:
                d = (fb_tech['created_at'] - fb_hr['created_at']).total_seconds() / 86400
                if d >= 0:
                    hr_to_tech_deltas.append(d)

            # 4. Technical Round -> Case Study
            if fb_tech and fb_case:
                d = (fb_case['created_at'] - fb_tech['created_at']).total_seconds() / 86400
                if d >= 0:
                    tech_to_case_deltas.append(d)

            # 5. Technical Round -> Final Round
            if fb_tech and fb_final:
                d = (fb_final['created_at'] - fb_tech['created_at']).total_seconds() / 86400
                if d >= 0:
                    tech_to_final_deltas.append(d)

            # 6. Case Study -> Final Round
            if fb_case and fb_final:
                d = (fb_final['created_at'] - fb_case['created_at']).total_seconds() / 86400
                if d >= 0:
                    case_to_final_deltas.append(d)

            note = app_notes.get(app_id)

            # 7. Final Round -> Under HR Review
            if fb_final and note:
                d = (note['created_at'] - fb_final['created_at']).total_seconds() / 86400
                if d >= 0:
                    final_to_review_deltas.append(d)

            # 8. Final Round -> Management / Client Round
            if fb_final and fb_mgt:
                d = (fb_mgt['created_at'] - fb_final['created_at']).total_seconds() / 86400
                if d >= 0:
                    final_to_mgt_deltas.append(d)

            # 9. Management / Client Round -> Under HR Review
            if fb_mgt and note:
                d = (note['created_at'] - fb_mgt['created_at']).total_seconds() / 86400
                if d >= 0:
                    mgt_to_review_deltas.append(d)

            # 8. Under HR Review -> Selected
            if note:
                last_fb = fb_mgt or fb_final or fb_case or fb_tech or fb_hr
                if last_fb:
                    d = (note['created_at'] - last_fb['created_at']).total_seconds() / 86400
                    if d >= 0:
                        review_to_selected_deltas.append(d)

            # 9. Selected -> Approval Note
            if note:
                selected_to_note_deltas.append(0.1)

            # 10. Approval Note -> Approved
            if note and note['approved_at']:
                d = (note['approved_at'] - note['created_at']).total_seconds() / 86400
                if d >= 0:
                    note_to_approved_deltas.append(d)

            hist = app_annexures.get(app_id, [])
            ann_created = next((h for h in hist if h['action'] == 'created'), None)
            ann_approved = next((h for h in hist if h['action'] == 'approved'), None)

            # 11. Approved -> Annexure
            if note and note['approved_at'] and ann_created:
                d = (ann_created['created_at'] - note['approved_at']).total_seconds() / 86400
                if d >= 0:
                    approved_to_annexure_deltas.append(d)

            # 12. Annexure -> Approved Annexure
            if ann_created and ann_approved:
                d = (ann_approved['created_at'] - ann_created['created_at']).total_seconds() / 86400
                if d >= 0:
                    annexure_to_approved_annexure_deltas.append(d)

            off_list = app_offers.get(app_id, [])
            offer = next((o for o in off_list if o['sent_at']), None)

            # 13. Approved Annexure -> Offer Sent
            if ann_approved and offer:
                d = (offer['sent_at'] - ann_approved['created_at']).total_seconds() / 86400
                if d >= 0:
                    approved_annexure_to_offer_sent_deltas.append(d)

            # 14. Offer Sent -> Offer Accepted / Rejected
            if offer:
                offer_resp_time = offer['completed_at'] or offer['signed_at'] or offer['updated_at']
                d = (offer_resp_time - offer['sent_at']).total_seconds() / 86400
                if d >= 0:
                    offer_sent_to_accepted_or_rejected_deltas.append(d)

            # 15. Offer Accepted -> Joining Pending
            if offer and (offer['completed_at'] or offer['signed_at'] or offer['status'] in ['completed', 'signed']):
                accepted_to_joining_pending_deltas.append(0.1)

            # 16. Joining Pending -> Joined
            if status == 'joined' and offer:
                offer_resp_time = offer['completed_at'] or offer['signed_at'] or offer['updated_at']
                d = (updated_at - offer_resp_time).total_seconds() / 86400
                if d >= 0:
                    joining_pending_to_joined_deltas.append(d)

        stage_times_wrapper = calc_stage_turnaround_time(app_qs)
        stage_days = {st['stage']: st['avg_days_in_stage'] for st in stage_times_wrapper.get('stages', [])}

        fallback_days = {
            'short_to_hr': stage_days.get('shortlisted') or stage_days.get('interview_pending_1') or 1.5,
            'hr_to_tech': stage_days.get('interview_pending_1') or stage_days.get('interview_pending_2') or 2.0,
            'tech_to_case': stage_days.get('interview_pending_2') or stage_days.get('interview_pending_3') or 2.5,
            'tech_to_final': stage_days.get('interview_pending_2') or stage_days.get('interview_pending_final') or 3.0,
            'case_to_final': stage_days.get('interview_pending_3') or stage_days.get('interview_pending_final') or 2.0,
            'final_to_review': stage_days.get('interview_pending_final') or stage_days.get('consolidated_result_review') or 1.5,
            'final_to_mgt': stage_days.get('interview_pending_final') or stage_days.get('interview_pending_management_client') or 2.0,
            'mgt_to_review': stage_days.get('interview_pending_management_client') or stage_days.get('consolidated_result_review') or 1.5,
            'review_to_selected': stage_days.get('consolidated_result_review') or 1.0,
            'selected_to_note': 0.1,
            'note_to_approved': stage_days.get('approval_pending') or 2.0,
            'approved_to_annexure': stage_days.get('salary_annexure_prep') or 1.5,
            'annexure_to_approved_annexure': stage_days.get('salary_annexure_review') or 2.0,
            'approved_annexure_to_offer_sent': stage_days.get('offer_pending') or 1.5,
            'offer_sent_to_accepted_or_rejected': stage_days.get('offer_sent') or 3.0,
            'accepted_to_joining_pending': 0.1,
            'joining_pending_to_joined': stage_days.get('joining_pending') or 15.0,
        }

        avg_between = [
            {
                'from_round': 'CV Received',
                'to_round': 'Shortlisted',
                'avg_days': cv_to_short_days or 1.0,
                'num_applications': len(cv_to_short_deltas)
            },
            {
                'from_round': 'Shortlisted',
                'to_round': 'HR Round',
                'avg_days': round(sum(short_to_hr_deltas) / len(short_to_hr_deltas), 2) if short_to_hr_deltas else fallback_days['short_to_hr'],
                'num_applications': len(short_to_hr_deltas)
            },
            {
                'from_round': 'HR Round',
                'to_round': 'Technical Round',
                'avg_days': round(sum(hr_to_tech_deltas) / len(hr_to_tech_deltas), 2) if hr_to_tech_deltas else fallback_days['hr_to_tech'],
                'num_applications': len(hr_to_tech_deltas)
            },
            {
                'from_round': 'Technical Round',
                'to_round': 'Case Study',
                'avg_days': round(sum(tech_to_case_deltas) / len(tech_to_case_deltas), 2) if tech_to_case_deltas else fallback_days['tech_to_case'],
                'num_applications': len(tech_to_case_deltas)
            },
            {
                'from_round': 'Technical Round',
                'to_round': 'Final Round',
                'avg_days': round(sum(tech_to_final_deltas) / len(tech_to_final_deltas), 2) if tech_to_final_deltas else fallback_days['tech_to_final'],
                'num_applications': len(tech_to_final_deltas)
            },
            {
                'from_round': 'Case Study',
                'to_round': 'Final Round',
                'avg_days': round(sum(case_to_final_deltas) / len(case_to_final_deltas), 2) if case_to_final_deltas else fallback_days['case_to_final'],
                'num_applications': len(case_to_final_deltas)
            },
            {
                'from_round': 'Final Round',
                'to_round': 'Under HR Review',
                'avg_days': round(sum(final_to_review_deltas) / len(final_to_review_deltas), 2) if final_to_review_deltas else fallback_days['final_to_review'],
                'num_applications': len(final_to_review_deltas)
            },
            {
                'from_round': 'Final Round',
                'to_round': 'Management / Client Round',
                'avg_days': round(sum(final_to_mgt_deltas) / len(final_to_mgt_deltas), 2) if final_to_mgt_deltas else fallback_days['final_to_mgt'],
                'num_applications': len(final_to_mgt_deltas)
            },
            {
                'from_round': 'Management / Client Round',
                'to_round': 'Under HR Review',
                'avg_days': round(sum(mgt_to_review_deltas) / len(mgt_to_review_deltas), 2) if mgt_to_review_deltas else fallback_days['mgt_to_review'],
                'num_applications': len(mgt_to_review_deltas)
            },
            {
                'from_round': 'Under HR Review',
                'to_round': 'Selected',
                'avg_days': round(sum(review_to_selected_deltas) / len(review_to_selected_deltas), 2) if review_to_selected_deltas else fallback_days['review_to_selected'],
                'num_applications': len(review_to_selected_deltas)
            },
            {
                'from_round': 'Selected',
                'to_round': 'Approval Note',
                'avg_days': round(sum(selected_to_note_deltas) / len(selected_to_note_deltas), 2) if selected_to_note_deltas else fallback_days['selected_to_note'],
                'num_applications': len(selected_to_note_deltas)
            },
            {
                'from_round': 'Approval Note',
                'to_round': 'Approved',
                'avg_days': round(sum(note_to_approved_deltas) / len(note_to_approved_deltas), 2) if note_to_approved_deltas else fallback_days['note_to_approved'],
                'num_applications': len(note_to_approved_deltas)
            },
            {
                'from_round': 'Approved',
                'to_round': 'Annexure',
                'avg_days': round(sum(approved_to_annexure_deltas) / len(approved_to_annexure_deltas), 2) if approved_to_annexure_deltas else fallback_days['approved_to_annexure'],
                'num_applications': len(approved_to_annexure_deltas)
            },
            {
                'from_round': 'Annexure',
                'to_round': 'Approved Annexure',
                'avg_days': round(sum(annexure_to_approved_annexure_deltas) / len(annexure_to_approved_annexure_deltas), 2) if annexure_to_approved_annexure_deltas else fallback_days['annexure_to_approved_annexure'],
                'num_applications': len(annexure_to_approved_annexure_deltas)
            },
            {
                'from_round': 'Approved Annexure',
                'to_round': 'Offer Sent',
                'avg_days': round(sum(approved_annexure_to_offer_sent_deltas) / len(approved_annexure_to_offer_sent_deltas), 2) if approved_annexure_to_offer_sent_deltas else fallback_days['approved_annexure_to_offer_sent'],
                'num_applications': len(approved_annexure_to_offer_sent_deltas)
            },
            {
                'from_round': 'Offer Sent',
                'to_round': 'Offer Accepted / Rejected',
                'avg_days': round(sum(offer_sent_to_accepted_or_rejected_deltas) / len(offer_sent_to_accepted_or_rejected_deltas), 2) if offer_sent_to_accepted_or_rejected_deltas else fallback_days['offer_sent_to_accepted_or_rejected'],
                'num_applications': len(offer_sent_to_accepted_or_rejected_deltas)
            },
            {
                'from_round': 'Offer Accepted',
                'to_round': 'Joining Pending',
                'avg_days': round(sum(accepted_to_joining_pending_deltas) / len(accepted_to_joining_pending_deltas), 2) if accepted_to_joining_pending_deltas else fallback_days['accepted_to_joining_pending'],
                'num_applications': len(accepted_to_joining_pending_deltas)
            },
            {
                'from_round': 'Joining Pending',
                'to_round': 'Joined',
                'avg_days': round(sum(joining_pending_to_joined_deltas) / len(joining_pending_to_joined_deltas), 2) if joining_pending_to_joined_deltas else fallback_days['joining_pending_to_joined'],
                'num_applications': len(joining_pending_to_joined_deltas)
            }
        ]
        section5['avg_time_between_rounds_days'] = avg_between

        # Round completion analytics with "Not Moved" and "Unassigned" logic
        # Prefetch related data for efficiency
        round_feedbacks = feedback_qs.select_related('job_application', 'job_application__job', 'job_application__job__mrf').prefetch_related(
            'job_application__job__assigned_internal_hrs',
            'job_application__job__assigned_consultancies',
            'job_application__job__mrf__technical_interviewers'
        )

        # Mapping of round types to statuses that belong to that SPECIFIC round.
        # If a candidate passes a round but their application status is still within this list,
        # it means they haven't advanced to the next round's bucket.
        round_belonging_map = {
            'hr_round': ['shortlisted', 'interview_pending_1', 'interview_done_1', 'interview_rejected_1'],
            'technical_round': ['interview_next_2', 'interview_pending_2', 'interview_done_2', 'interview_rejected_2'],
            'case_study_round': ['interview_next_3', 'interview_pending_3', 'interview_done_3', 'interview_rejected_3'],
            'final_round': ['interview_next_final', 'interview_pending_final', 'interview_done_final', 'interview_rejected_final'],
            'management_client_round': ['interview_next_management_client', 'interview_pending_management_client', 'interview_done_management_client', 'interview_rejected_management_client', 'consolidated_result_review'],
        }

        # Candidate-centric aggregation per round
        # This ensures we count each candidate once per round, even if they have multiple interviews.
        app_round_stats = defaultdict(lambda: {
            'passed': False,
            'unassigned': False,
            'status': None,
            'job': None
        })

        # Track total interviews separately if needed, but for completion rates, candidate-round pairs are more standard.
        stats_by_round = defaultdict(lambda: {'completed': 0, 'passed': 0, 'not_moved': 0, 'unassigned': 0, 'rejected': 0})

        # Group feedback results by candidate and round
        for fb in round_feedbacks:
            r_type = fb.interview_round
            if not r_type: continue
            
            app_id = fb.job_application_id
            key = (app_id, r_type)
            stats = app_round_stats[key]
            
            stats['status'] = fb.job_application.status
            stats['job'] = fb.job_application.job

            if fb.is_selected in ['hire', 'strong_hire']:
                stats['passed'] = True

            # Unassigned check for this specific interview
            job = fb.job_application.job
            mrf = job.mrf
            assigned_identities = getattr(job, '_assigned_identities_cache', None)
            
            if assigned_identities is None:
                assigned_identities = set()
                # Job FKs
                for u in [job.assigned_to_internal_hr, job.assigned_to_consultancy, job.posted_by, job.closed_by]:
                    if u:
                        if u.name: assigned_identities.add(u.name.lower().strip())
                        if u.email: assigned_identities.add(u.email.lower().strip())
                
                # Job M2Ms
                for u in job.assigned_internal_hrs.all():
                    if u.name: assigned_identities.add(u.name.lower().strip())
                    if u.email: assigned_identities.add(u.email.lower().strip())
                for u in job.assigned_consultancies.all():
                    if u.name: assigned_identities.add(u.name.lower().strip())
                    if u.email: assigned_identities.add(u.email.lower().strip())

                # MRF String fields (Names and Emails)
                mrf_names = [mrf.technical_interview_1, mrf.technical_interview_2, mrf.final_interview, mrf.requested_by_name]
                for n in mrf_names:
                    if n: assigned_identities.add(n.lower().strip())
                
                mrf_emails = [mrf.interviewer_email_1, mrf.interviewer_email_2, mrf.interviewer_email_3, mrf.interviewer_email_final, mrf.interviewer_email_management_client]
                for e in mrf_emails:
                    if e: assigned_identities.add(e.lower().strip())
                
                # MRF FKs (Interviewer objects)
                mrf_fk_interviewers = [mrf.hr_interviewer, mrf.case_study_interviewer, mrf.final_interviewer, mrf.management_client_interviewer]
                for u in mrf_fk_interviewers:
                    if u:
                        if u.name: assigned_identities.add(u.name.lower().strip())
                        if u.email: assigned_identities.add(u.email.lower().strip())
                
                # MRF M2M Technical Interviewers
                for ti in mrf.technical_interviewers.all():
                    if ti.name: assigned_identities.add(ti.name.lower().strip())
                    if ti.email: assigned_identities.add(ti.email.lower().strip())
                
                job._assigned_identities_cache = assigned_identities

            fb_name = fb.interviewer_name.lower().strip() if fb.interviewer_name else None
            # If name is missing or not in assigned list, mark as unassigned
            if not fb_name or fb_name not in assigned_identities:
                stats['unassigned'] = True

        # Round progression order for checking if next interview was actually taken
        round_order = ['hr_round', 'technical_round', 'case_study_round', 'final_round', 'management_client_round']
        candidate_rounds = set(app_round_stats.keys())
        
        # Post-interview statuses (candidate has moved beyond all interview rounds)
        post_interview_statuses = {
            'consolidated_result_review', 'selected', 'approval_pending', 'approved', 'approval_rejected',
            'salary_annexure_prep', 'salary_annexure_review', 'approved_annexure', 'rejected_annexure',
            'offer_pending', 'offer_sent', 'offer_accepted', 'offer_rejected',
            'docs_pending', 'docs_uploaded', 'review_docs', 'docs_approved', 'docs_incomplete', 'docs_unclear',
            'joining_pending', 'joining_poned', 'joined'
        }

        # Aggregation with core identity: Completed = Shortlisted (Passes) + Rejected (Fails)
        for (app_id, r_type), data in app_round_stats.items():
            stats_by_round[r_type]['completed'] += 1
            
            if data['passed']:
                stats_by_round[r_type]['passed'] += 1
                
                # "Not Moved": Passed this round but NO actual interview taken in any later round
                current_idx = round_order.index(r_type) if r_type in round_order else -1
                has_next_interview = False
                
                # Check if feedback exists in any subsequent round
                if current_idx >= 0:
                    for later_round in round_order[current_idx + 1:]:
                        if (app_id, later_round) in candidate_rounds:
                            has_next_interview = True
                            break
                
                # Also check if they've reached post-interview stages (selected, offer, joined, etc.)
                if not has_next_interview and data['status'] in post_interview_statuses:
                    has_next_interview = True
                
                if not has_next_interview:
                    stats_by_round[r_type]['not_moved'] += 1
            else:
                stats_by_round[r_type]['rejected'] += 1

            if data['unassigned']:
                stats_by_round[r_type]['unassigned'] += 1

        # Count interviews scheduled per round (pending + already completed)
        round_pending_statuses = {
            'hr_round': 'interview_pending_1',
            'technical_round': 'interview_pending_2',
            'case_study_round': 'interview_pending_3',
            'final_round': 'interview_pending_final',
            'management_client_round': 'interview_pending_management_client',
        }
        scheduled_by_round = {}
        for round_key, pending_status in round_pending_statuses.items():
            # Currently pending (scheduled but not yet done)
            currently_pending = app_qs.filter(status=pending_status).count()
            # Already completed (have feedback) = stats_by_round completed count
            already_done = stats_by_round[round_key]['completed'] if round_key in stats_by_round else 0
            scheduled_by_round[round_key] = currently_pending + already_done

        completion_rates = []
        ordered_round_keys = ['hr_round', 'technical_round', 'case_study_round', 'final_round', 'management_client_round']
        
        # Iterate in specific requested order: HR -> Technical -> Case Study -> Final -> Management
        for round_key in ordered_round_keys:
            if round_key in stats_by_round or scheduled_by_round.get(round_key, 0) > 0:
                stats = stats_by_round[round_key]
                completed = stats['completed']
                total_passed = stats['passed']
                rejected = stats['rejected']
                not_moved = stats['not_moved']
                unassigned = stats['unassigned']
                
                pending_count = scheduled_by_round.get(round_key, 0) - completed
                completion_rates.append({
                    'round_type': round_display.get(round_key, round_key),
                    'total_scheduled': scheduled_by_round.get(round_key, 0),
                    'pending': pending_count,
                    'completed': completed,
                    'shortlisted': total_passed,
                    'rejected': rejected,
                    'not_moved_to_next': not_moved,
                    'unassigned_interviewer_count': unassigned,
                    'pass_rate_percentage': round(total_passed / completed * 100, 2) if completed else 0
                })
        
        # Append any miscellaneous rounds if they somehow exist in the data
        for round_key, stats in stats_by_round.items():
            if round_key not in ordered_round_keys:
                completed = stats['completed']
                total_passed = stats['passed']
                rejected = stats['rejected']
                not_moved = stats['not_moved']
                unassigned = stats['unassigned']
                completion_rates.append({
                    'round_type': round_display.get(round_key, round_key),
                    'total_scheduled': scheduled_by_round.get(round_key, 0),
                    'pending': scheduled_by_round.get(round_key, 0) - completed,
                    'completed': completed,
                    'shortlisted': total_passed,
                    'rejected': rejected,
                    'not_moved_to_next': not_moved,
                    'unassigned_interviewer_count': unassigned,
                    'pass_rate_percentage': round(total_passed / completed * 100, 2) if completed else 0
                })
        section5['round_completion_rate'] = completion_rates

        # Pending count average (as percentage of total_scheduled) across all rounds
        pending_pcts = [round((r['pending'] / r['total_scheduled'] * 100), 2) if r['total_scheduled'] else 0 for r in completion_rates]
        section5['pending_count_percentage'] = round(sum(pending_pcts) / len(pending_pcts), 2) if pending_pcts else 0

        # Add pending_count_avg percentage to each round
        for i, rate in enumerate(completion_rates):
            rate['pending_count_percentage'] = round((rate['pending'] / rate['total_scheduled'] * 100), 2) if rate['total_scheduled'] else 0

        # Highest reschedule by source
        # Primary: use reschedule_count from JobApplication
        # Fallback: count from Booking table (candidates with >1 booking = rescheduled)
        reschedule_by_source = (
            app_qs.filter(reschedule_count__gt=0)
            .values('source')
            .annotate(
                total_reschedules=Sum('reschedule_count'),
                candidate_count=Count('id')
            )
            .order_by('-total_reschedules')
        )
        SOURCE_DISPLAY = dict(JobApplication.SOURCE_CHOICES)

        if reschedule_by_source.exists():
            reschedule_source_list = [
                {
                    'source': r['source'],
                    'source_display': SOURCE_DISPLAY.get(r['source'], r['source']),
                    'total_reschedules': r['total_reschedules'],
                    'candidate_count': r['candidate_count'],
                }
                for r in reschedule_by_source
            ]
        else:
            # Fallback: count from Booking table - candidates with multiple bookings
            from booking.models import Booking as BookingModel
            booking_counts = (
                BookingModel.objects.filter(candidate__in=app_qs)
                .values('candidate_id')
                .annotate(booking_count=Count('id'))
                .filter(booking_count__gt=1)
            )
            # Group by source
            rescheduled_app_ids = [b['candidate_id'] for b in booking_counts]
            reschedule_fallback = (
                app_qs.filter(id__in=rescheduled_app_ids)
                .values('source')
                .annotate(
                    candidate_count=Count('id'),
                )
                .order_by('-candidate_count')
            )
            # For each source, sum up (booking_count - 1) as reschedule count
            booking_map = {b['candidate_id']: b['booking_count'] - 1 for b in booking_counts}
            source_reschedule_totals = defaultdict(int)
            for app in app_qs.filter(id__in=rescheduled_app_ids).values('id', 'source'):
                source_reschedule_totals[app['source']] += booking_map.get(app['id'], 0)

            reschedule_source_list = [
                {
                    'source': r['source'],
                    'source_display': SOURCE_DISPLAY.get(r['source'], r['source']),
                    'total_reschedules': source_reschedule_totals.get(r['source'], 0),
                    'candidate_count': r['candidate_count'],
                }
                for r in reschedule_fallback
            ]
            reschedule_source_list.sort(key=lambda x: x['total_reschedules'], reverse=True)

        section5['highest_reschedule_by_source'] = reschedule_source_list


        # Stage turnaround times (calculated from sequential transition turnaround times)
        avg_between = section5.get('avg_time_between_rounds_days', [])
        avg_times = [
            {
                'stage': f"{item['from_round']} -> {item['to_round']}",
                'avg_days': item['avg_days']
            }
            for item in avg_between
            if item.get('avg_days', 0.0) > 0.0 and item.get('num_applications', 0) > 0
        ]
        if avg_times:
            slowest = max(avg_times, key=lambda x: x['avg_days'])
            fastest = min(avg_times, key=lambda x: x['avg_days'])
            section5['slowest_stage'] = {'stage_name': slowest['stage'], 'avg_days': slowest['avg_days']}
            section5['fastest_stage'] = {'stage_name': fastest['stage'], 'avg_days': fastest['avg_days']}
        else:
            section5['slowest_stage'] = {'stage_name': 'N/A', 'avg_days': 0.0}
            section5['fastest_stage'] = {'stage_name': 'N/A', 'avg_days': 0.0}
        return section5

    def calc_approval_note_analytics(self, job_qs, date_range, target_user=None):
        section6 = {}
        date_from, date_to = date_range
        from datetime import datetime, time
        from django.utils import timezone
        
        base_q = Q(candidate__job__in=job_qs)
        if target_user:
            base_q &= (Q(manager=target_user) | Q(created_by=target_user))
            
        def make_date_q(field_name):
            q = Q()
            if date_from:
                dt_from = timezone.make_aware(datetime.combine(date_from, time.min))
                q &= Q(**{f"{field_name}__gte": dt_from})
            if date_to:
                dt_to = timezone.make_aware(datetime.combine(date_to, time.max))
                q &= Q(**{f"{field_name}__lte": dt_to})
            return q

        created_q = make_date_q('created_at')
        approved_q = make_date_q('approved_at')
        
        # Notes sent in period
        sent_qs = ApprovalNote.objects.filter(base_q & created_q)
        section6['total_approval_notes_sent'] = sent_qs.count()
        
        # Notes approved in period (regardless of when sent)
        approved_statuses = ['approved','docs_pending','docs_uploaded','review_docs','docs_approved','salary_annexure_prep','salary_annexure_review','approved_annexure','offer_pending','offer_sent','offer_accepted','offer_rejected','joining_pending','joined','joining_poned','docs_incomplete','docs_unclear']
        approved_qs = ApprovalNote.objects.filter(base_q & approved_q & Q(status__in=approved_statuses))
        section6['approval_notes_approved'] = approved_qs.count()
        
        # Notes rejected in period
        rejected_qs = ApprovalNote.objects.filter(base_q & make_date_q('rejected_at') & Q(status='approval_rejected'))
        section6['approval_notes_rejected'] = rejected_qs.count()
        
        # Notes currently pending (snapshot)
        section6['approval_notes_pending'] = ApprovalNote.objects.filter(base_q & Q(status='approval_pending')).count()

        if approved_qs.exists():
            avg = approved_qs.aggregate(avg=Avg(F('approved_at') - F('created_at')))['avg']
            section6['avg_time_to_approve_days'] = round(avg.total_seconds() / 86400, 2) if avg else 0
        else:
            section6['avg_time_to_approve_days'] = 0

        delayed_threshold = timezone.now() - timedelta(hours=48)
        section6['delayed_approval_notes'] = ApprovalNote.objects.filter(base_q & Q(status='approval_pending', created_at__lt=delayed_threshold)).count()

        # Approver stats
        # Group by manager for all notes that had activity in the period
        activity_q = Q()
        if date_from or date_to:
            activity_q = make_date_q('updated_at')
            
        approver_stats_qs = ApprovalNote.objects.filter(base_q & activity_q)
        
        approver_stats = approver_stats_qs.values('manager_id','manager__name').annotate(
            sent=Count('id', filter=created_q),
            approved=Count('id', filter=approved_q & Q(status__in=approved_statuses)),
            rejected=Count('id', filter=make_date_q('rejected_at') & Q(status='approval_rejected')),
        )
        by_approver = []
        for a in approver_stats:
            mgr_id = a['manager_id']
            mgr_approved = approved_qs.filter(manager_id=mgr_id)
            avg_days = 0
            if mgr_approved.exists():
                avg_d = mgr_approved.aggregate(avg=Avg(F('approved_at') - F('created_at')))['avg']
                avg_days = round(avg_d.total_seconds() / 86400, 2) if avg_d else 0
            by_approver.append({
                'approver_name': a['manager__name'] or 'Unknown',
                'approver_id': mgr_id,
                'sent': a['sent'],
                'approved': a['approved'],
                'rejected': a['rejected'],
                'avg_days': avg_days
            })
        section6['approval_notes_by_approver'] = by_approver
        return section6

    def calc_document_offer_process_timeline(self, broad_job_qs, date_range=None, company=None):
        from onboarding.models import JobApplicationDocument, ApprovalNote, OfferDocument
        from collections import defaultdict
        from datetime import datetime, time
        from django.utils import timezone
        
        section7 = {}
        date_from, date_to = date_range if date_range else (None, None)
        
        def make_date_q(field='updated_at'):
            q = Q()
            if date_from:
                dt_from = timezone.make_aware(datetime.combine(date_from, time.min))
                q &= Q(**{f"{field}__gte": dt_from})
            if date_to:
                dt_to = timezone.make_aware(datetime.combine(date_to, time.max))
                q &= Q(**{f"{field}__lte": dt_to})
            return q

        date_q = make_date_q('updated_at')
        
        # Get application IDs that had ANY activity in these documents in the date range
        app_ids = set()
        
        if date_from or date_to:
            offer_apps = OfferDocument.objects.filter(application__job__in=broad_job_qs).filter(date_q).values_list('application_id', flat=True)
            jad_apps = JobApplicationDocument.objects.filter(job_application__job__in=broad_job_qs).filter(
                date_q | make_date_q('annexure_uploaded_at') | make_date_q('annexure_approved_at')
            ).values_list('job_application_id', flat=True)
            note_apps = ApprovalNote.objects.filter(candidate__job__in=broad_job_qs).filter(date_q).values_list('candidate_id', flat=True)
            
            app_ids.update(offer_apps)
            app_ids.update(jad_apps)
            app_ids.update(note_apps)
        else:
            # No date filter, get all apps from broad_job_qs
            app_ids = set(JobApplication.objects.filter(job__in=broad_job_qs).values_list('id', flat=True)[:5000])
        
        app_ids = list(app_ids)[:5000] # safety limit
        
        offers = list(OfferDocument.objects.filter(application_id__in=app_ids).values('application_id', 'created_at', 'sent_at', 'signed_at', 'completed_at', 'status', 'updated_at'))
        jads = list(JobApplicationDocument.objects.filter(job_application_id__in=app_ids).values('job_application_id', 'joining_docs_status', 'created_at', 'updated_at', 'annexure_uploaded_at', 'annexure_approved_at', 'salary_annexure_approved'))
        notes = list(ApprovalNote.objects.filter(candidate_id__in=app_ids, status__in=['approved','docs_pending','docs_uploaded','review_docs','docs_approved','salary_annexure_prep','salary_annexure_review','approved_annexure','offer_pending','offer_sent','offer_accepted','offer_rejected','joining_pending','joined','joining_poned','docs_incomplete','docs_unclear'], approved_at__isnull=False).values('candidate_id', 'approved_at'))
        
        apps_data = defaultdict(dict)
        for j in jads: apps_data[j['job_application_id']]['jad'] = j
        for n in notes: apps_data[n['candidate_id']]['note'] = n
        for o in offers: apps_data[o['application_id']]['offer'] = o
            
        req_to_up_days, up_to_appr_days, appr_to_sal_days, sal_to_appr_days, offer_create_days, offer_sent_to_resp_days, offer_internal_appr_days = [], [], [], [], [], [], []

        for app_id, data in apps_data.items():
            jad, note, offer = data.get('jad'), data.get('note'), data.get('offer')
            if jad:
                td = (jad['updated_at'] - jad['created_at']).total_seconds() / 86400
                if td >= 0:
                    if jad['joining_docs_status'] == 'uploaded': req_to_up_days.append(td)
                    elif jad['joining_docs_status'] in ['approved', 'review_docs']:
                        req_to_up_days.append(td/2); up_to_appr_days.append(td/2)
            if note and jad and jad.get('annexure_uploaded_at'):
                td = (jad['annexure_uploaded_at'] - note['approved_at']).total_seconds() / 86400
                if td >= 0: appr_to_sal_days.append(td)
            if jad and jad.get('salary_annexure_approved') and jad.get('annexure_approved_at') and jad.get('annexure_uploaded_at'):
                td = (jad['annexure_approved_at'] - jad['annexure_uploaded_at']).total_seconds() / 86400
                if td >= 0: sal_to_appr_days.append(td)
            if note and offer and note.get('approved_at'):
                td = (offer['created_at'] - note['approved_at']).total_seconds() / 86400
                if td >= 0: offer_create_days.append(td)
            if offer:
                start, sent, comp, signed = offer.get('created_at'), offer.get('sent_at'), offer.get('completed_at'), offer.get('signed_at')
                end_resp = comp or signed or offer.get('updated_at')
                if sent and start:
                    td = (sent - start).total_seconds() / 86400
                    if td >= 0: offer_internal_appr_days.append(td)
                if offer['status'] in ['completed', 'signed', 'declined'] and sent and end_resp:
                    td = (end_resp - sent).total_seconds() / 86400
                    if td >= 0: offer_sent_to_resp_days.append(td)

        def avg_d(lst): return round(sum(lst) / len(lst), 2) if lst else 0.0
        section7.update({
            'avg_time_document_request_to_upload_days': avg_d(req_to_up_days),
            'avg_time_document_upload_to_approval_days': avg_d(up_to_appr_days),
            'avg_time_approval_to_salary_annexure_days': avg_d(appr_to_sal_days),
            'avg_time_salary_annexure_to_approval_days': avg_d(sal_to_appr_days),
            'avg_time_to_offer_letter_creation_days': avg_d(offer_create_days),
            'avg_time_offer_letter_to_approval_days': avg_d(offer_internal_appr_days),
            'avg_time_offer_letter_sent_to_response_days': avg_d(offer_sent_to_resp_days)
        })

        joined_q = Q(job__in=broad_job_qs, status='joined')
        if date_from or date_to:
            joined_q &= make_date_q('updated_at')
        joined_apps = JobApplication.objects.filter(joined_q)
        
        durations_days = [(app.updated_at - app.job.mrf.created_at).total_seconds() / 86400 for app in joined_apps if app.job and app.job.mrf and app.job.mrf.created_at and app.updated_at]
        section7['full_pipeline_avg_days'] = round(sum(durations_days) / len(durations_days), 2) if durations_days else 0
        
        stages = [('Document Request to Upload', section7['avg_time_document_request_to_upload_days']), ('Document Upload to Approval', section7['avg_time_document_upload_to_approval_days']), ('Approval to Salary Annexure', section7['avg_time_approval_to_salary_annexure_days']), ('Salary Annexure to Approval', section7['avg_time_salary_annexure_to_approval_days']), ('Offer Letter Creation', section7['avg_time_to_offer_letter_creation_days']), ('Offer Letter Approval/Sent', section7['avg_time_offer_letter_to_approval_days']), ('Offer Sent to Response', section7['avg_time_offer_letter_sent_to_response_days'])]
        bottleneck = max(stages, key=lambda x: x[1]) if any(s[1] > 0 for s in stages) else ('None', 0.0)
        section7['bottleneck_stage'] = {'stage_name': bottleneck[0], 'avg_days': bottleneck[1]}
        return section7

    def calc_overall_summary_kpis(self, mrf_qs, job_qs, app_qs, platform_app_qs, referral_qs, company, date_range=None):
        section8 = {}
        base_app_qs = JobApplication.objects.filter(job__company=company)
        
        section8['total_candidates'] = app_qs.count() + platform_app_qs.filter(is_touched=False).count() + referral_qs.filter(is_touched=False).count()
        section8['total_positions_filled'] = sum(j.positions_filled for j in job_qs)
        section8['total_positions_open'] = sum((j.no_of_positions - j.positions_filled) for j in job_qs)
        section8['total_positions'] = sum(j.no_of_positions for j in job_qs)
        section8['total_joining_pending_job_open_positions'] = sum(j.no_of_positions - j.positions_filled for j in job_qs if j.status == 'joining_pending')
        section8['total_joining_pending_job_count'] = sum(1 for j in job_qs if j.status == 'joining_pending')
        
        offer_sent_statuses = ['offer_sent', 'offer_accepted', 'offer_rejected', 'joined', 'joining_pending', 'joining_poned']
        offer_accepted_statuses = ['offer_accepted', 'joined', 'joining_poned', 'joining_pending']
        
        offer_sent_c = app_qs.filter(status__in=offer_sent_statuses).count()
        offer_accepted_c = app_qs.filter(status__in=offer_accepted_statuses).count()
        section8['overall_offer_acceptance_rate'] = round((offer_accepted_c / offer_sent_c * 100), 2) if offer_sent_c else 0

        joined_apps = app_qs.filter(status='joined')
        durations_hire = [(app.updated_at - app.created_at).total_seconds() / 86400 for app in joined_apps if app.updated_at and app.created_at]
        # section8['tat_days'] = round(sum(durations_hire) / len(durations_hire), 2) if durations_hire else 0

        # Inject new TAT metrics
        # Updated to use app_qs so that user_id and other filters are respected
        tat_metrics = calc_joining_tat(app_qs)
        section8["partial_joining_tat_days"] = tat_metrics["partial_joining_tat_days"]
        section8["final_joining_tat_days"] = tat_metrics["final_joining_tat_days"]

        # Source breakdown
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

        # Active counts (ignores date filter to show live snapshot)
        # Using company-wide querysets for these KPIs to avoid being affected by the date range selected
        base_job_qs = Job.objects.filter(company=company)
        section8['active_jobs_count'] = base_job_qs.filter(is_active=True).count()
        section8['active_consultancies_count'] = User.objects.filter(role='consultancy', company=company, is_active=True).filter(assigned_jobs__in=base_job_qs).distinct().count()
        section8['active_internal_hrs_count'] = User.objects.filter(role__in=['hr', 'hr_manager'], company=company, is_active=True).filter(assigned_internal_jobs__in=base_job_qs).distinct().count()

        # Last 30 days metrics (Fixed: uses company-wide apps_qs instead of filtered app_qs)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        section8['cvs_last_30_days'] = app_qs.filter(created_at__gte=thirty_days_ago).count()
        section8['offers_last_30_days'] = OfferDocument.objects.filter(
            application__in=app_qs,
            sent_at__gte=thirty_days_ago
        ).count()

        # Joining Pending in next 30 / 60 days
        from datetime import date
        today = date.today()
        joining_pending_qs = app_qs.filter(
            status='joining_pending',
            joining_date__isnull=False,
            joining_date__gte=today,
        )
        section8['joining_pending_next_30_days'] = joining_pending_qs.filter(
            joining_date__lte=today + timedelta(days=30)
        ).count()
        section8['joining_pending_next_60_days'] = joining_pending_qs.filter(
            joining_date__lte=today + timedelta(days=60)
        ).count()

        return section8

    def get_sections(self):
        """Override this in subclasses to return only allowed sections."""
        return []

    def get_role_filters(self, user):
        """Override this in subclasses to return filters."""
        return Q(), Q(), Q()

    def calc_summary_totals(self, mrf_qs, job_qs, app_qs, platform_app_qs, referral_qs, broad_job_qs=None):
        """Standard summary totals for quick dashboard cards.
        broad_job_qs: All jobs assigned to the user (ignoring date filter).
        Used for total_jobs so filtered-by-user views show all their jobs, not just period-created ones.
        """
        # Use broad_job_qs for total counts if provided (user_id filter scenario)
        jobs_for_count = job_qs
        
        direct_count = app_qs.count()
        platform_count = platform_app_qs.filter(is_touched=False).count()
        referral_count = referral_qs.filter(is_touched=False).count()
        combined_count = direct_count + platform_count + referral_count

        return {
            "total_mrfs": mrf_qs.count(),
            "total_mrfs_on_hold": mrf_qs.filter(status='on_hold').count(),
            "total_jobs": jobs_for_count.count(),
            "total_jobs_on_hold": jobs_for_count.filter(status='on_hold').count(),
            "total_combined_cv_count": combined_count,
            "cv_counts": {
                "direct_applications": direct_count,
                "platform_applications": platform_count,
                "referrals": referral_count,
                "combined": combined_count,
                "total": direct_count + platform_count + referral_count
            },
            # "total_open_positions": sum((j.no_of_positions - j.positions_filled) for j in jobs_for_count),
            "total_open_positions": sum(j.remaining_positions() for j in jobs_for_count),"jobs_by_assignment": {
                "hr_only": jobs_for_count.filter(Q(status='assigned_to_internal_hr') | Q(previous_status='assigned_to_internal_hr'), assigned_to_internal_hr__isnull=False, assigned_to_consultancy__isnull=True).count(),
                "consultancy_only": jobs_for_count.filter(Q(status='assigned_to_consultancy') | Q(previous_status='assigned_to_consultancy'), assigned_to_consultancy__isnull=False, assigned_to_internal_hr__isnull=True).count(),
                "both": jobs_for_count.filter(Q(status='assigned_to_both') | Q(previous_status='assigned_to_both'), assigned_to_internal_hr__isnull=False, assigned_to_consultancy__isnull=False).count()
            }
        }

    def get(self, request):
        ctx, err = self.get_common_querysets(request)
        if err:
            return Response({"detail": err}, status=status.HTTP_400_BAD_REQUEST)

        mrf_qs, job_qs, broad_job_qs, app_qs, platform_app_qs, referral_qs, company, date_filter, target_user, date_from, date_to = ctx["mrf_qs"], ctx["job_qs"], ctx["broad_job_qs"], ctx["app_qs"], ctx["platform_app_qs"], ctx["referral_qs"], ctx["company"], ctx["date_filter"], ctx.get("target_user"), ctx.get("date_from"), ctx.get("date_to")
        allowed_sections = self.get_sections()

        # Resolve Interviewer Entities using Email via Booking table for reliability
        interviewer_app_ids = None
        interviewer_names = []
        if target_user:
            from slots.models import Interviewer
            from booking.models import Booking
            interviewers = Interviewer.objects.filter(email=target_user.email)
            interviewer_names = list(interviewers.values_list('name', flat=True))
            
            # Get all application IDs where this user was an interviewer or attendee
            interviewer_app_ids = list(Booking.objects.filter(
                Q(interviewer__in=interviewers) | Q(attendees__in=interviewers)
            ).values_list('candidate_id', flat=True).distinct())

            if target_user.name and target_user.name not in interviewer_names:
                interviewer_names.append(target_user.name)
        
        # Determine which sections to return
        requested_sections = request.query_params.get('sections', '').split(',')
        if requested_sections == ['']:
            requested_sections = allowed_sections
        else:
            requested_sections = [s for s in requested_sections if s in allowed_sections]

        data = {
            "summary": self.calc_summary_totals(mrf_qs, job_qs, app_qs, platform_app_qs, referral_qs, broad_job_qs),
            "user_details": UserSerializer(ctx["target_user"]).data if ctx.get("target_user") else UserSerializer(ctx["user"]).data
        }

        # Inject new TAT metrics
        tat_metrics = calc_joining_tat(app_qs)
        data["partial_joining_tat_days"] = tat_metrics["partial_joining_tat_days"]
        data["final_joining_tat_days"] = tat_metrics["final_joining_tat_days"]
        if 'mrf_analytics' in requested_sections:
            data['mrf_analytics'] = self.calc_mrf_analytics(mrf_qs)
        if 'job_assignment_analytics' in requested_sections:
            target_user_id = ctx['target_user'].id if ctx.get('target_user') else None
            data['job_assignment_analytics'] = self.calc_job_assignment_analytics(job_qs, request.user.role, target_user_id)
        # Calculate Total Completed Rounds (synchronized with Section 5)
        # Uses the same logic as calc_interview_round_time_analytics
        fb_filter = Q(job_application__job__in=broad_job_qs)
        from datetime import datetime, time
        from django.utils import timezone
        if date_from:
            dt_from = timezone.make_aware(datetime.combine(date_from, time.min))
            fb_filter &= Q(created_at__gte=dt_from)
        if date_to:
            dt_to = timezone.make_aware(datetime.combine(date_to, time.max))
            fb_filter &= Q(created_at__lte=dt_to)
        if interviewer_app_ids is not None: fb_filter &= Q(job_application_id__in=interviewer_app_ids)
        total_completed_interviews = InterviewFeedback.objects.filter(fb_filter).count()

        if 'cv_resume_source_analytics' in requested_sections:
            data['cv_resume_source_analytics'] = self.calc_cv_resume_source_analytics(app_qs, platform_app_qs, referral_qs, total_completed_interviews)
        if 'candidate_pipeline_funnel' in requested_sections:
            data['candidate_pipeline_funnel'] = self.calc_candidate_pipeline_funnel(app_qs, target_user, interviewer_app_ids)
        if 'interview_round_time_analytics' in requested_sections:
            data['interview_round_time_analytics'] = self.calc_interview_round_time_analytics(app_qs, (date_from, date_to), company, interviewer_app_ids, broad_job_qs)
        if 'approval_note_analytics' in requested_sections:
            data['approval_note_analytics'] = self.calc_approval_note_analytics(broad_job_qs, (date_from, date_to), target_user)
        if 'document_offer_process_timeline' in requested_sections:
            # Pass company to filter OfferDocuments correctly
            data['document_offer_process_timeline'] = self.calc_document_offer_process_timeline(broad_job_qs, (date_from, date_to), company)
        if 'overall_summary_kpis' in requested_sections:
            data['overall_summary_kpis'] = self.calc_overall_summary_kpis(mrf_qs, job_qs, app_qs, platform_app_qs, referral_qs, company, (date_from, date_to))

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
        app_q = Q(job__assigned_to_internal_hr=user) | Q(job__assigned_internal_hrs=user) | Q(job__posted_by=user) | Q(job__closed_by=user) | Q(submitted_by=user)
        mrf_q = Q(requested_by=user) | Q(approvals__approver=user)
        return mrf_q, job_q, app_q

    def get_sections(self):
        return ['cv_resume_source_analytics', 'candidate_pipeline_funnel', 'interview_round_time_analytics', 'overall_summary_kpis','job_assignment_analytics']

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
        app_q = (Q(application_link__created_by_id=user) | Q(submitted_by=user))
        return Q(id=None), job_q, app_q

    def get_sections(self):
        return ['candidate_pipeline_funnel', 'overall_summary_kpis', 'job_assignment_analytics']


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
                return Response({"detail": "No feedback has been given till now."}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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