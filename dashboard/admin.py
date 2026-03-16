from django.contrib import admin
from .models import RecruitmentCost, CandidateExperienceFeedback


@admin.register(RecruitmentCost)
class RecruitmentCostAdmin(admin.ModelAdmin):
    list_display = [
        'job', 'consultancy_fees', 'ads_expense',
        'referral_bonus', 'employee_package', 'total_cost',
        'created_at',
    ]
    list_filter = ['company']
    search_fields = ['job__job_title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CandidateExperienceFeedback)
class CandidateExperienceFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'application', 'feedback_type', 'nps_score',
        'overall_satisfaction', 'interviewer_quality',
        'is_submitted', 'submitted_at', 'created_at',
    ]
    list_filter = ['feedback_type', 'is_submitted', 'overall_satisfaction', 'stage_reached']
    search_fields = ['application__candidate_name', 'feedback_token']
    readonly_fields = ['feedback_token', 'created_at']
