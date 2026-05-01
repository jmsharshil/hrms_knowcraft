"""
Utility functions for computing all 10 dashboard metrics.
Each function receives a filtered queryset (by company/date/department/job)
and returns a dictionary for its metric section.
"""

from django.db.models import Count, Avg, Q, F, Sum, Case, When, IntegerField, FloatField
from django.db.models.functions import TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta

from jobs.models import JobApplication, Job
from slots.models import InterviewFeedback


# ---------- ordered pipeline stages for pass-through ----------
PIPELINE_STAGES = [
    'received',
    'shortlisted',
    'interview_pending_1',
    'interview_done_1',
    'interview_next_2',
    'interview_pending_2',
    'interview_done_2',
    'interview_next_3',
    'interview_pending_3',
    'interview_done_3',
    'interview_next_final',
    'interview_pending_final',
    'interview_done_final',
    'interview_next_management_client',
    'interview_pending_management_client',
    'interview_done_management_client',
    'consolidated_result_review',
    'selected',
    'approval_pending',
    'approved',
    'salary_annexure_prep',
    'salary_annexure_review',
    'approved_annexure',
    'offer_pending',
    'offer_sent',
    'offer_accepted',
    'joining_pending',
    'joined',
]

STATUS_DISPLAY = dict(JobApplication.STATUS_CHOICES)


def _index_of(status):
    """Return the index of a status in the pipeline, or -1 if missing."""
    try:
        return PIPELINE_STAGES.index(status)
    except ValueError:
        return -1


# ──────────────────────────────────────────────────────────────
# 1. STAGE PASS-THROUGH RATES
# ──────────────────────────────────────────────────────────────
def calc_stage_passthrough_rates(apps_qs):
    """
    For each consecutive stage pair, compute:
      rate = (# apps that reached ≥ next_stage) / (# apps that reached ≥ current_stage) × 100
    """
    total_apps = apps_qs.count()
    if total_apps == 0:
        return {"total_applications": 0, "stages": []}

    # Count how many applications ever reached each stage or beyond
    reached = {}
    for idx, stage in enumerate(PIPELINE_STAGES):
        q = Q()
        for s in PIPELINE_STAGES[idx:]:
            q |= Q(status=s)
        reached[stage] = apps_qs.filter(q).count()

    stages = []
    for i in range(len(PIPELINE_STAGES) - 1):
        current = PIPELINE_STAGES[i]
        nxt = PIPELINE_STAGES[i + 1]
        prior_count = reached.get(current, 0)
        next_count = reached.get(nxt, 0)
        rate = round((next_count / prior_count) * 100, 2) if prior_count else 0
        stages.append({
            "from_stage": current,
            "from_stage_display": STATUS_DISPLAY.get(current, current),
            "to_stage": nxt,
            "to_stage_display": STATUS_DISPLAY.get(nxt, nxt),
            "prior_count": prior_count,
            "advanced_count": next_count,
            "rate_percent": rate,
        })

    return {"total_applications": total_apps, "stages": stages}


# ──────────────────────────────────────────────────────────────
# 2. STAGE-LEVEL TURNAROUND TIME
# ──────────────────────────────────────────────────────────────
def calc_stage_turnaround_time(apps_qs):
    """
    For apps still in a given stage, compute avg days sitting there.
    Uses `updated_at` as the time the app entered the current stage.
    """
    now = timezone.now()
    results = []

    stage_groups = (
        apps_qs
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )

    for sg in stage_groups:
        stage = sg['status']
        count = sg['count']
        # Average age = avg(now - updated_at) for apps at this stage
        avg_age = (
            apps_qs
            .filter(status=stage)
            .aggregate(avg_days=Avg(
                (now - F('updated_at')),
            ))
        )
        avg_seconds = avg_age['avg_days']
        if avg_seconds and hasattr(avg_seconds, 'total_seconds'):
            avg_days = round(avg_seconds.total_seconds() / 86400, 1)
        else:
            avg_days = 0

        results.append({
            "stage": stage,
            "stage_display": STATUS_DISPLAY.get(stage, stage),
            "applications_count": count,
            "avg_days_in_stage": avg_days,
        })

    return {"stages": results}


# ──────────────────────────────────────────────────────────────
# 2.5 JOINING TURNAROUND TIME (TAT)
# ──────────────────────────────────────────────────────────────
def calc_joining_tat(apps_qs):
    from django.db.models import F, Avg, ExpressionWrapper, DurationField
    from django.db.models.functions import Cast
    from django.db.models import DateField
    
    # 1. Partial Joining Avg Time - TAT (Job Open -> Offer Accepted)
    partial_apps = apps_qs.filter(
        offer_accepted_date__isnull=False,
        job__created_at__isnull=False
    ).annotate(
        job_open_date_only=Cast('job__created_at', DateField())
    )
    
    partial_avg = partial_apps.aggregate(
        avg_tat=Avg(ExpressionWrapper(
            F('offer_accepted_date') - F('job_open_date_only'),
            output_field=DurationField()
        ))
    )['avg_tat']
    
    partial_days = max(0, round(partial_avg.total_seconds() / 86400, 1)) if partial_avg else 0
    
    # 2. Final Joining Avg Time - TAT (Job Open -> Offered Joining Date)
    final_apps = apps_qs.filter(
        joining_date__isnull=False,
        job__created_at__isnull=False
    ).annotate(
        job_open_date_only=Cast('job__created_at', DateField())
    )
    
    final_avg = final_apps.aggregate(
        avg_tat=Avg(ExpressionWrapper(
            F('joining_date') - F('job_open_date_only'),
            output_field=DurationField()
        ))
    )['avg_tat']
    
    final_days = max(0, round(final_avg.total_seconds() / 86400, 1)) if final_avg else 0
    
    return {
        "partial_joining_tat_days": partial_days,
        "final_joining_tat_days": final_days
    }


# ──────────────────────────────────────────────────────────────
# 3. OFFER-TO-JOIN RATIO
# ──────────────────────────────────────────────────────────────
def calc_offer_to_join_ratio(apps_qs):
    offer_released = apps_qs.filter(
        status__in=['offer_sent', 'offer_accepted', 'offer_rejected',
                    'joining_pending', 'joining_poned', 'joined','offer_pending']
    ).count()

    # Count only those whose current status reached offer_sent or beyond
    offer_accepted = apps_qs.filter(
        status__in=['offer_accepted', 'joining_pending', 'joining_poned', 'joined']
    ).count()

    ratio = round((offer_accepted / offer_released) * 100, 2) if offer_released else 0

    return {
        "offer_released": offer_released,
        "offer_accepted": offer_accepted,
        "ratio_percent": ratio,
    }


# ──────────────────────────────────────────────────────────────
# 4. INTERVIEW NO-SHOW & RESCHEDULE RATES
# ──────────────────────────────────────────────────────────────
def calc_interview_no_show_reschedule(apps_qs, total_count=None):
    agg = apps_qs.aggregate(
        total_no_shows=Sum('no_show_count'),
        total_reschedules=Sum('reschedule_count'),
    )
    # If total_count is provided externally (e.g. from interview feedback totals), use it.
    # Otherwise fallback to counting unique candidates in interview stages.
    interview_apps = total_count if total_count is not None else apps_qs.exclude(
        status__in=['received', 'duplicate_rejected', 'shortlisted', 'rejected']
    ).count()

    no_shows = agg['total_no_shows'] or 0
    reschedules = agg['total_reschedules'] or 0

    return {
        "total_interviews": interview_apps,
        "total_no_shows": no_shows,
        "total_reschedules": reschedules,
        "no_show_rate_percent": round((no_shows / interview_apps) * 100, 2) if interview_apps else 0,
        "reschedule_rate_percent": round((reschedules / interview_apps) * 100, 2) if interview_apps else 0,
    }


# ──────────────────────────────────────────────────────────────
# 5. COST ROI / COST PER HIRE
# ──────────────────────────────────────────────────────────────
def calc_cost_per_hire(jobs_qs):
    from .models import RecruitmentCost

    costs = RecruitmentCost.objects.filter(job__in=jobs_qs)

    agg = costs.aggregate(
        total_consultancy=Sum('consultancy_fees'),
        total_ads=Sum('ads_expense'),
        total_referral=Sum('referral_bonus'),
        total_package=Sum('employee_package'),
    )

    total_consultancy = agg['total_consultancy'] or 0
    total_ads = agg['total_ads'] or 0
    total_referral = agg['total_referral'] or 0
    total_package = agg['total_package'] or 0
    total_cost = total_consultancy + total_ads + total_referral + total_package

    total_filled = jobs_qs.aggregate(total=Sum('positions_filled'))['total'] or 0
    cost_per_hire = round(float(total_cost) / total_filled, 2) if total_filled else 0

    return {
        "consultancy_fees": float(total_consultancy),
        "ads_expense": float(total_ads),
        "referral_bonus": float(total_referral),
        "employee_package": float(total_package),
        "total_cost": float(total_cost),
        "total_positions_filled": total_filled,
        "cost_per_hire": cost_per_hire,
    }


# ──────────────────────────────────────────────────────────────
# 6. SOURCE QUALITY / SOURCE ROI
# ──────────────────────────────────────────────────────────────
def calc_source_quality(apps_qs):
    source_stats = (
        apps_qs
        .values('source')
        .annotate(
            total=Count('id'),
            joined_count=Count('id', filter=Q(status='joined')),
            shortlisted_count=Count('id', filter=Q(status__in=[
                'shortlisted', 'interview_pending_1', 'interview_done_1',
                'interview_next_2', 'interview_pending_2', 'interview_done_2',
                'interview_next_3', 'interview_pending_3', 'interview_done_3',
                'interview_next_final', 'interview_pending_final', 'interview_done_final',
                'interview_next_management_client', 'interview_pending_management_client',
                'interview_done_management_client', 'consolidated_result_review',
                'selected', 'approval_pending', 'approved',
                'salary_annexure_prep', 'salary_annexure_review', 'approved_annexure',
                'offer_pending', 'offer_sent', 'offer_accepted',
                'docs_pending', 'docs_uploaded', 'review_docs', 'docs_approved',
                'joining_pending', 'joining_poned', 'joined',
            ])),
            offer_count=Count('id', filter=Q(status__in=[
                'offer_pending', 'offer_sent', 'offer_accepted', 'offer_rejected',
                'joining_pending', 'joining_poned', 'joined',
            ])),
        )
        .order_by('-joined_count')
    )

    SOURCE_DISPLAY = dict(JobApplication.SOURCE_CHOICES)

    results = []
    for s in source_stats:
        total = s['total']
        results.append({
            "source": s['source'],
            "source_display": SOURCE_DISPLAY.get(s['source'], s['source']),
            "total_applications": total,
            "shortlisted": s['shortlisted_count'],
            "offers": s['offer_count'],
            "joined": s['joined_count'],
            "closure_rate_percent": round((s['joined_count'] / total) * 100, 2) if total else 0,
        })

    return {"sources": results}


# ──────────────────────────────────────────────────────────────
# 7. AGING BY STAGE  (shortlisted but interview not conducted)
# ──────────────────────────────────────────────────────────────
def calc_aging_by_stage(apps_qs):
    now = timezone.now()

    # Applications that are shortlisted but haven't moved to interview
    aging_apps = apps_qs.filter(status='shortlisted')

    results = []
    for app in aging_apps.select_related('job')[:100]:  # cap for performance
        days = (now - app.updated_at).total_seconds() / 86400
        results.append({
            "application_id": str(app.id),
            "candidate_name": app.candidate_name or "N/A",
            "job_title": app.job.job_title,
            "job_id": str(app.job.id),
            "status": app.status,
            "days_aging": round(days, 1),
            "updated_at": app.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

    results.sort(key=lambda x: x['days_aging'], reverse=True)

    return {
        "total_aging": len(results),
        "applications": results,
    }


# ──────────────────────────────────────────────────────────────
# 8. OFFER ANALYTICS  (declined offers & rejection reasons)
# ──────────────────────────────────────────────────────────────
def calc_offer_analytics(apps_qs):
    declined = apps_qs.filter(status='offer_rejected')

    reasons = (
        declined
        .values('rejection_reason')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    reason_list = []
    for r in reasons:
        reason_list.append({
            "reason": r['rejection_reason'] or "Not specified",
            "count": r['count'],
        })

    # breakdown by job
    by_job = (
        declined
        .values('job__job_title', 'job__id')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    job_list = []
    for j in by_job:
        job_list.append({
            "job_id": str(j['job__id']),
            "job_title": j['job__job_title'],
            "declined_count": j['count'],
        })

    return {
        "total_offers_declined": declined.count(),
        "decline_reasons": reason_list,
        "by_job": job_list,
    }
# ──────────────────────────────────────────────────────────────
# 9. RECRUITER PRODUCTIVITY & WORKLOAD
# ──────────────────────────────────────────────────────────────
def calc_recruiter_productivity(apps_qs, target_user_id=None):
    """
    Per recruiter (HR user who submitted CVs):
      - total CVs submitted
      - CVs this week
      - interviews scheduled this week
      - offers this month
    """
    now = timezone.now()
    week_start = now - timedelta(days=now.weekday())  # Monday
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    recruiter_filter = Q(submitted_by__isnull=False)
    if target_user_id:
        recruiter_filter &= Q(submitted_by__id=target_user_id)

    recruiter_stats = (
        apps_qs
        .filter(recruiter_filter)
        .values('submitted_by__id', 'submitted_by__name', 'submitted_by__email')
        .annotate(
            total_cvs=Count('id'),
            cvs_this_week=Count('id', filter=Q(created_at__gte=week_start)),
            interviews_this_week=Count('id', filter=Q(
                created_at__gte=week_start,
                status__in=[
                    'interview_pending_1', 'interview_done_1',
                    'interview_pending_2', 'interview_done_2',
                    'interview_pending_3', 'interview_done_3',
                    'interview_pending_final', 'interview_done_final',
                    'interview_pending_management_client', 'interview_done_management_client',
                ],
            )),
            offers_this_month=Count('id', filter=Q(
                created_at__gte=month_start,
                status__in=['offer_sent', 'offer_accepted', 'offer_rejected'],
            )),
        )
        .order_by('-total_cvs')
    )

    results = []
    for rs in recruiter_stats:
        results.append({
            "recruiter_id": str(rs['submitted_by__id']),
            "recruiter_name": rs['submitted_by__name'] or "N/A",
            "recruiter_email": rs['submitted_by__email'] or "N/A",
            "total_cvs": rs['total_cvs'],
            "cvs_this_week": rs['cvs_this_week'],
            "interviews_this_week": rs['interviews_this_week'],
            "offers_this_month": rs['offers_this_month'],
        })

    return {"recruiters": results}


# ──────────────────────────────────────────────────────────────
# 10. CANDIDATE EXPERIENCE  (NPS + CSAT + per-question averages)
# ──────────────────────────────────────────────────────────────
def calc_candidate_experience(apps_qs):
    """
    Computes:
      - NPS  = %Promoters(9-10) − %Detractors(0-6)  from Q1
      - CSAT = %(Satisfied + Very Satisfied)          from Q2
      - Averages for Q3-Q6
      - Stage-reached distribution
      - Recent open feedback
    """
    from .models import CandidateExperienceFeedback
    from django.db.models import Case, When, IntegerField

    feedbacks = CandidateExperienceFeedback.objects.filter(
        application__in=apps_qs,
        is_submitted=True,
    )

    total = feedbacks.count()

    if total == 0:
        return {
            "total_responses": 0,
            "nps": None,
            "csat_percent": None,
            "averages": {},
            "stage_reached_distribution": [],
            "recent_feedbacks": [],
        }

    # Numeric mappings for averages
    satisfaction_numeric = Case(
        When(overall_satisfaction='very_dissatisfied', then=1),
        When(overall_satisfaction='dissatisfied', then=2),
        When(overall_satisfaction='satisfied', then=3),
        When(overall_satisfaction='very_satisfied', then=4),
        default=None,
        output_field=IntegerField(null=True)
    )

    ease_numeric = Case(
        When(process_ease='very_difficult', then=1),
        When(process_ease='difficult', then=2),
        When(process_ease='easy', then=3),
        When(process_ease='very_easy', then=4),
        default=None,
        output_field=IntegerField(null=True)
    )

    communication_numeric = Case(
        When(communication='very_dissatisfied', then=1),
        When(communication='dissatisfied', then=2),
        When(communication='satisfied', then=3),
        When(communication='very_satisfied', then=4),
        default=None,
        output_field=IntegerField(null=True)
    )

    interviewer_numeric = Case(
        When(interviewer_quality='very_poor', then=1),
        When(interviewer_quality='poor', then=2),
        When(interviewer_quality='average', then=3),
        When(interviewer_quality='good', then=4),
        When(interviewer_quality='excellent', then=5),
        default=None,
        output_field=IntegerField(null=True)
    )

    speed_numeric = Case(
        When(recruitment_speed='very_slow', then=1),
        When(recruitment_speed='slow', then=2),
        When(recruitment_speed='acceptable', then=3),
        When(recruitment_speed='fast', then=4),
        When(recruitment_speed='very_fast', then=5),
        default=None,
        output_field=IntegerField(null=True)
    )

    # ── NPS from Q1 (nps_score 0-10) ──
    promoters = feedbacks.filter(nps_score__gte=9).count()
    detractors = feedbacks.filter(nps_score__lte=6).count()
    passives = total - promoters - detractors

    nps_value = max(0, round(((promoters - detractors) / total) * 100, 1))

    # ── CSAT from Q2 (overall_satisfaction: satisfied or very_satisfied) ──
    satisfied = feedbacks.filter(
        overall_satisfaction__in=['satisfied', 'very_satisfied']
    ).count()
    csat_percent = round((satisfied / total) * 100, 1)

    # ── Averages for scaled questions ──
    averages_agg = feedbacks.aggregate(
        avg_nps=Avg('nps_score'),
        avg_overall_satisfaction=Avg(satisfaction_numeric),
        avg_process_ease=Avg(ease_numeric),
        avg_communication=Avg(communication_numeric),
        avg_interviewer_quality=Avg(interviewer_numeric),
        avg_recruitment_speed=Avg(speed_numeric),
    )

    averages = {}
    for key, val in averages_agg.items():
        averages[key] = round(val, 2) if val is not None else None

    # ── Stage reached distribution (Q6b) ──
    stage_dist = (
        feedbacks
        .exclude(stage_reached='')
        .values('stage_reached')
        .annotate(count=Count('id'))
        .order_by('stage_reached')
    )

    STAGE_DISPLAY = dict(CandidateExperienceFeedback.STAGE_REACHED_CHOICES)
    stage_list = [
        {
            "stage": s['stage_reached'],
            "stage_display": STAGE_DISPLAY.get(s['stage_reached'], s['stage_reached']),
            "count": s['count'],
        }
        for s in stage_dist
    ]

    # ── Recent open feedback (last 10) ──
    recent = feedbacks.order_by('-submitted_at')[:10]
    recent_list = []
    for fb in recent.select_related('application'):
        recent_list.append({
            "candidate_name": fb.application.candidate_name or "N/A",
            "feedback_type": fb.feedback_type,
            "nps_score": fb.nps_score,
            "nps_category": fb.nps_category,
            "overall_satisfaction": fb.get_overall_satisfaction_display() if fb.overall_satisfaction else None,
            "improvement_suggestion": fb.improvement_suggestion,
            "most_frustrating": fb.most_frustrating,
            "better_handling": fb.better_handling,
            "submitted_at": fb.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if fb.submitted_at else None,
        })

    return {
        "total_responses": total,
        "nps": {
            "score": nps_value,
            "promoters": promoters,
            "passives": passives,
            "detractors": detractors,
            "promoter_percent": round((promoters / total) * 100, 1),
            "detractor_percent": round((detractors / total) * 100, 1),
        },
        "csat_percent": csat_percent,
        "averages": averages,
        "stage_reached_distribution": stage_list,
        "recent_feedbacks": recent_list,
    }

