from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from .models import Slot, Interviewer, InterviewFeedback, InterviewLocation


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'start', 'end', 'is_booked', 'interviewer_count',
        'interviewer_list_preview'
    )
    list_filter = ('is_booked', 'start', 'end')
    search_fields = ('interviewers__name', 'interviewers__email')
    readonly_fields = ('id',)
    filter_horizontal = ('interviewers',)
    date_hierarchy = 'start'
    ordering = ('-start',)

    fieldsets = (
        ('Slot Details', {
            'fields': ('id', 'start', 'end', 'is_booked', 'interviewers')
        }),
    )

    def interviewer_count(self, obj):
        return obj.interviewers.count()
    interviewer_count.short_description = '# Interviewers'

    def interviewer_list_preview(self, obj):
        names = [i.name for i in obj.interviewers.all()[:3]]
        if len(names) > 3:
            names.append('...')
        return ', '.join(names) or '—'
    interviewer_list_preview.short_description = 'Interviewers'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('interviewers')


@admin.register(Interviewer)
class InterviewerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'email', 'company', 'is_active',
        'subscription_status', 'subscription_expiry'
    )
    list_filter = ('is_active', 'company', 'subscription_expiry')
    search_fields = ('name', 'email', 'company__name')
    readonly_fields = ('id', 'subscription_id')
    actions = ['soft_delete_selected']

    fieldsets = (
        ('Personal Info', {
            'fields': ('id', 'name', 'email', 'phone', 'company')
        }),
        ('Subscription & Status', {
            'fields': ('subscription_id', 'subscription_expiry', 'is_active'),
            'classes': ('collapse',),
        }),
    )

    def subscription_status(self, obj):
        if obj.subscription_expiry and obj.subscription_expiry > timezone.now():
            return format_html('<span style="color:green;">Active</span>')
        return format_html('<span style="color:red;">Expired/Inactive</span>')
    subscription_status.short_description = 'Subscription'

    def soft_delete_selected(self, request, queryset):
        count = 0
        for interviewer in queryset:
            interviewer.soft_delete()
            count += 1
        self.message_user(request, f"Soft-deleted {count} interviewer(s).")
    soft_delete_selected.short_description = "Soft delete selected interviewers (mark inactive)"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


@admin.register(InterviewFeedback)
class InterviewFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'candidate_link', 'interview_round', 'is_selected',
        'round_average', 'created_at'
    )
    list_filter = (
        'interview_round', 'is_selected', 'created_at',
        'hr_round_avg_rating', 'tech_round_avg_rating'
    )
    search_fields = (
        'job_application__candidate_name', 'job_application__candidate_email',
        'interviewer_name', 'interview_round'
    )
    readonly_fields = (
        'id', 'created_at', 'hr_round_avg_rating', 'tech_round_avg_rating',
        'case_study_round_avg_rating', 'final_round_avg_rating',
        'management_client_round_rating'
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        ('Core Details', {
            'fields': (
                'id', 'job_application', 'interview_round', 'is_selected',
                'interview_date', 'interviewer_name', 'department', 'designation'
            )
        }),
        ('Average Ratings (Computed)', {
            'fields': (
                'hr_round_avg_rating', 'tech_round_avg_rating',
                'case_study_round_avg_rating', 'final_round_avg_rating',
                'management_client_round_rating'
            ),
            'classes': ('collapse',),
        }),
        ('Key Ratings', {
            'fields': (
                'communication_rating', 'technical_skill_rating',
                'attitude_intent_rating', 'team_handling_rating',
                'stability_rating', 'problem_solving_rating',
                'analytical_thinking_rating', 'cultural_fit_rating',
                'competency_rating', 'interpersonal_skills_rating',
                'leadership_skills_rating', 'learning_agility_rating',
                'problem_solving_critical_thinking_decision_making_rating',
                'business_acumen_industry_understanding_rating',
                'ownership_accountibility_rating'
            ),
            'classes': ('collapse',),
        }),
        ('Remarks & Qualitative', {
            'fields': (
                'learning_agility_rating_remark',
                'problem_solving_critical_thinking_decision_making_rating_remark',
                'business_acumen_industry_understanding_rating_remark',
                'ownership_accountibility_rating_remark',
                'leadership_skills_rating_remark',
                'interpersonal_skills_rating_remark',
                'competency_rating_remark',
                'communication_rating_remark',
                'technical_skill_rating_remark',
                'attitude_intent_rating_remark',
                'team_handling_rating_remark',
                'stability_rating_remark',
                'problem_solving_rating_remark',
                'analytical_thinking_rating_remark',
                'cultural_fit_rating_remark',
                'qualification', 'comments', 'strengths', 'goals',
                'behavioral_cultural_fit', 'areas_of_improvement',
                'strength_areas_of_improvement', 'goals_development_plan',
                'behavioral', 'personal_background', 'role_responsibility'
            ),
            'classes': ('collapse',),
        }),
        ('Candidate Background', {
            'fields': (
                'current_organization', 'current_organization_location',
                'current_designation', 'current_location', 'work_mode',
                'job_change_reason', 'notice_period', 'current_ctc',
                'expected_ctc', 'bond', 'motivation_for_change_career_aspirations',
                'achievement_orientation_impact', 'satbility_reliability_commitment',
                'hometown', 'preferred_location'
            ),
            'classes': ('collapse',),
        }),
    )

    def candidate_link(self, obj):
        if obj.job_application:
            url = reverse("admin:jobs_jobapplication_change", args=[obj.job_application.id])
            return format_html('<a href="{}">{}</a>', url, obj.job_application.candidate_name)
        return "—"
    candidate_link.short_description = 'Candidate'
    candidate_link.admin_order_field = 'job_application__candidate_name'

    def round_average(self, obj):
        """Use the model's get_round_avg() and color-code it."""
        avg = getattr(obj, 'get_round_avg', lambda: 0)()
        if avg >= 4.0:
            color = 'green'
        elif avg >= 3.0:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color:{};">{:.2f}</span>', color, avg)
    round_average.short_description = 'Round Avg'
    round_average.admin_order_field = 'hr_round_avg_rating'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('job_application')


@admin.register(InterviewLocation)
class InterviewLocationAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'city', 'is_default', 'is_active',
        'full_address_preview', 'google_maps_link_display'
    )
    list_filter = ('is_active', 'is_default', 'city', 'state', 'country', 'created_at')
    search_fields = ('name', 'full_address', 'city', 'company__name')
    readonly_fields = ('id', 'full_address', 'google_maps_link', 'created_at')
    actions = ['soft_delete_selected']

    fieldsets = (
        ('Location Details', {
            'fields': (
                'id', 'name', 'company', 'is_default', 'is_active',
                'address_line_1', 'address_line_2', 'city', 'state',
                'pincode', 'country'
            )
        }),
        ('Geo & Mapping', {
            'fields': (
                'latitude', 'longitude', 'place_id',
                'full_address', 'google_maps_link'
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def full_address_preview(self, obj):
        if obj.full_address:
            return (obj.full_address[:60] + '...') if len(obj.full_address) > 60 else obj.full_address
        return "—"
    full_address_preview.short_description = 'Full Address'

    def google_maps_link_display(self, obj):
        if obj.google_maps_link:
            return format_html('<a href="{}" target="_blank">🗺️ Map</a>', obj.google_maps_link)
        return "—"
    google_maps_link_display.short_description = 'Google Maps'

    def soft_delete_selected(self, request, queryset):
        count = 0
        for location in queryset:
            location.soft_delete()
            count += 1
        self.message_user(request, f"Soft-deleted {count} location(s).")
    soft_delete_selected.short_description = "Soft delete selected locations (mark inactive)"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')
