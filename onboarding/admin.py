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

admin.site.register(ApprovalNote)
admin.site.register(JobApplicationDocument, JobApplicationDocumentAdmin)
admin.site.register(SalaryAnnexure)
admin.site.register(SalaryComponent)
admin.site.register(SalaryAnnexureHistory)
# admin.site.register(DocuSignOffer)
admin.site.register(OfferDocument, OfferDocumentAdmin)