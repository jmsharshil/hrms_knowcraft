from django.contrib import admin
from .models import ApprovalNote,JobApplicationDocument,SalaryAnnexure,SalaryAnnexureHistory,SalaryComponent,OfferDocument

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
admin.site.register(SalaryAnnexure, SalaryAnnexureAdmin)
admin.site.register(SalaryComponent, SalaryComponentAdmin)
admin.site.register(SalaryAnnexureHistory, SalaryAnnexureHistoryAdmin)
# admin.site.register(DocuSignOffer)
admin.site.register(OfferDocument, OfferDocumentAdmin)