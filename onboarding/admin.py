from django.contrib import admin
from .models import (
    ApprovalNote, JobApplicationDocument, SalaryAnnexure, SalaryAnnexureHistory,
    SalaryComponent, OfferDocument, EmailLog, OnboardingForm, SurveyResponse, OnboardingCall,
    OnboardingTaskList, OnboardingTask, DocumentEsignTask
)

# Register your models here.

class JobApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_candidate_name', 'joining_docs_status', 'created_at')
    search_fields = ('job_application__candidate_name', 'job_application__candidate_email')
    list_filter = ('joining_docs_status', 'created_at')

    def get_candidate_name(self, obj):
        return obj.job_application.candidate_name if obj.job_application else ''
    get_candidate_name.short_description = 'Candidate Name'
    get_candidate_name.admin_order_field = 'job_application__candidate_name'

class OfferDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_candidate_name', 'status', 'sent_at', 'signed_at')
    search_fields = ('application__candidate_name', 'application__candidate_email', 'zoho_document_id')
    list_filter = ('status', 'created_at')

    def get_candidate_name(self, obj):
        return obj.application.candidate_name if obj.application else ''
    get_candidate_name.short_description = 'Candidate Name'
    get_candidate_name.admin_order_field = 'application__candidate_name'


class ApprovalNoteAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'get_candidate_name', 
        'get_candidate_email',
        'status', 
        'bgv_status',
        'manager',
        'created_by',
        'created_at',
        'approved_at',
    )
    search_fields = (
        'candidate__candidate_name', 
        'candidate__candidate_email',
        'candidate__candidate_phone',
        'manager__email',
        'manager__name',
        'created_by__email',
    )
    list_filter = (
        'status',
        'bgv_status',
        'manager',
        'created_by',
        'created_at',
        'approved_at',
        'rejected_at',
    )
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at', 'updated_at', 'approved_at', 'rejected_at')
    ordering = ('-created_at',)
    list_per_page = 50

    def get_candidate_name(self, obj):
        return obj.candidate.candidate_name if obj.candidate else ''
    get_candidate_name.short_description = 'Candidate Name'
    get_candidate_name.admin_order_field = 'candidate__candidate_name'

    def get_candidate_email(self, obj):
        return obj.candidate.candidate_email if obj.candidate else ''
    get_candidate_email.short_description = 'Candidate Email'
    get_candidate_email.admin_order_field = 'candidate__candidate_email'


class SalaryAnnexureAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_candidate_name',
        'get_candidate_email',
        'designation',
        'ctc_annual',
        'gross_monthly',
        'net_monthly',
        'status',
        'prepared_by',
        'reviewed_by',
        'effective_from',
        'revision_count',
        'created_at',
    )
    search_fields = (
        'job_application__candidate_name',
        'job_application__candidate_email',
        'job_application__candidate_phone',
        'designation',
        'prepared_by__email',
        'prepared_by__name',
        'reviewed_by__email',
    )
    list_filter = (
        'status',
        'prepared_by',
        'reviewed_by',
        'effective_from',
        'created_at',
        'updated_at',
    )
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 50
    list_editable = ('status',)

    def get_candidate_name(self, obj):
        return obj.job_application.candidate_name if obj.job_application else ''
    get_candidate_name.short_description = 'Candidate Name'
    get_candidate_name.admin_order_field = 'job_application__candidate_name'

    def get_candidate_email(self, obj):
        return obj.job_application.candidate_email if obj.job_application else ''
    get_candidate_email.short_description = 'Candidate Email'
    get_candidate_email.admin_order_field = 'job_application__candidate_email'


class SalaryAnnexureHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_candidate_name',
        'status',
        'created_by',
        'created_at',
    )
    search_fields = (
        'job_application__candidate_name',
        'job_application__candidate_email',
        'created_by__email',
        'created_by__name',
    )
    list_filter = (
        'status',
        'created_by',
        'created_at',
    )
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 50

    def get_candidate_name(self, obj):
        return obj.job_application.candidate_name if obj.job_application else ''
    get_candidate_name.short_description = 'Candidate Name'
    get_candidate_name.admin_order_field = 'job_application__candidate_name'


class SalaryComponentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'component_type',
        'monthly_amount',
        'annual_amount',
        'is_statutory',
        'order',
    )
    list_filter = ('component_type', 'is_statutory')
    search_fields = ('name', 'annexure__job_application__candidate_name')
    ordering = ('annexure', 'order')
    list_per_page = 100

admin.site.register(ApprovalNote, ApprovalNoteAdmin)
admin.site.register(JobApplicationDocument, JobApplicationDocumentAdmin)
# admin.site.register(SalaryAnnexure, SalaryAnnexureAdmin)
# admin.site.register(SalaryComponent, SalaryComponentAdmin)
# admin.site.register(SalaryAnnexureHistory, SalaryAnnexureHistoryAdmin)
# admin.site.register(DocuSignOffer)
admin.site.register(OfferDocument, OfferDocumentAdmin)


class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient_email', 'subject', 'status', 'sent_at', 'error_message')
    list_filter = ('status', 'sent_at')
    search_fields = ('recipient_email', 'subject', 'body_text', 'error_message')
    readonly_fields = ('sent_at',)
    date_hierarchy = 'sent_at'
    ordering = ('-sent_at',)
    list_per_page = 50
    list_select_related = ('job_application',)

admin.site.register(EmailLog, EmailLogAdmin)


class OnboardingFormAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_candidate_name', 'ticket_ref', 'designation',
        'department', 'work_from', 'employee_category', 'joining_date', 'created_at'
    )
    search_fields = (
        'job_application__candidate_name', 'job_application__candidate_email',
        'ticket_ref', 'first_name', 'last_name', 'crafter_id', 'personal_email_id'
    )
    list_filter = ('department', 'work_from', 'employee_category', 'site', 'created_at')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('job_application', 'submitted_by')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 50
    list_select_related = ('job_application', 'submitted_by')
    fieldsets = (
        ('Candidate & Submission Info', {
            'fields': ('id', 'job_application', 'submitted_by', 'ticket_ref', 'created_at')
        }),
        ('Candidate Details', {
            'fields': (
                'first_name', 'last_name', 'personal_email_id', 'contact_number',
                'current_address', 'crafter_id'
            )
        }),
        ('Role & Work Info', {
            'fields': (
                'designation', 'department', 'employee_category',
                'work_from', 'center_office_location', 'joining_date'
            )
        }),
        ('IT / Assets', {
            'fields': ('assets', 'site', 'mode_for_collecting_assets', 'team_manager')
        }),
        ('Communication', {
            'fields': ('subject', 'emails_to_notify', 'description', 'custom_notes')
        }),
    )

    def get_candidate_name(self, obj):
        return obj.job_application.candidate_name if obj.job_application else ''
    get_candidate_name.short_description = 'Candidate Name'
    get_candidate_name.admin_order_field = 'job_application__candidate_name'


class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_candidate_name', 'get_candidate_email',
        'survey_type', 'respondent_name', 'respondent_email', 'submitted_at'
    )
    search_fields = (
        'job_application__candidate_name', 'job_application__candidate_email',
        'respondent_name', 'respondent_email'
    )
    list_filter = ('survey_type', 'submitted_at')
    readonly_fields = ('id', 'submitted_at', 'responses')
    raw_id_fields = ('job_application',)
    date_hierarchy = 'submitted_at'
    ordering = ('-submitted_at',)
    list_per_page = 50
    list_select_related = ('job_application',)
    fieldsets = (
        ('Survey Info', {
            'fields': ('id', 'job_application', 'survey_type', 'submitted_at')
        }),
        ('Respondent', {
            'fields': ('respondent_name', 'respondent_email')
        }),
        ('Responses (JSON)', {
            'fields': ('responses',),
            'classes': ('collapse',)
        }),
    )

    def get_candidate_name(self, obj):
        return obj.job_application.candidate_name if obj.job_application else ''
    get_candidate_name.short_description = 'Candidate Name'
    get_candidate_name.admin_order_field = 'job_application__candidate_name'

    def get_candidate_email(self, obj):
        return obj.job_application.candidate_email if obj.job_application else ''
    get_candidate_email.short_description = 'Candidate Email'
    get_candidate_email.admin_order_field = 'job_application__candidate_email'


class OnboardingCallAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_candidate_name', 'call_type', 'organizer_email',
        'start_time', 'end_time', 'get_has_meeting_link', 'created_at'
    )
    search_fields = (
        'job_application__candidate_name', 'job_application__candidate_email',
        'organizer_email', 'meeting_id'
    )
    list_filter = ('call_type', 'created_at')
    readonly_fields = ('id', 'created_at', 'meeting_link')
    raw_id_fields = ('job_application',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 50
    list_select_related = ('job_application',)
    fieldsets = (
        ('Call Info', {
            'fields': ('id', 'job_application', 'call_type', 'created_at')
        }),
        ('Schedule', {
            'fields': ('organizer_email', 'start_time', 'end_time')
        }),
        ('Teams Meeting', {
            'fields': ('meeting_id', 'meeting_link')
        }),
    )

    def get_candidate_name(self, obj):
        return obj.job_application.candidate_name if obj.job_application else ''
    get_candidate_name.short_description = 'Candidate Name'
    get_candidate_name.admin_order_field = 'job_application__candidate_name'

    def get_has_meeting_link(self, obj):
        return bool(obj.meeting_link)
    get_has_meeting_link.short_description = 'Has Meeting Link'
    get_has_meeting_link.boolean = True


class OnboardingTaskListAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_application', 'name', 'created_at')
    search_fields = ('name', 'job_application__candidate_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_filter = ('created_at',)

class OnboardingTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_list', 'title', 'status', 'due_date', 'assigned_to')
    search_fields = ('title', 'task_list__job_application__candidate_name')
    list_filter = ('status', 'due_date', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')

admin.site.register(OnboardingForm, OnboardingFormAdmin)
admin.site.register(SurveyResponse, SurveyResponseAdmin)
admin.site.register(OnboardingCall, OnboardingCallAdmin)
admin.site.register(OnboardingTaskList, OnboardingTaskListAdmin)
admin.site.register(OnboardingTask, OnboardingTaskAdmin)

@admin.register(DocumentEsignTask)
class DocumentEsignTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_application', 'doc_type', 'status', 'created_at')
    search_fields = ('job_application__candidate_name', 'doc_type')
    list_filter = ('status', 'doc_type', 'created_at')
    readonly_fields = ('id', 'created_at')
