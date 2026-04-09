from django.contrib import admin
from .models import ApprovalNote,JobApplicationDocument,SalaryAnnexure,SalaryAnnexureHistory,SalaryComponent,DocuSignOffer
# Register your models here.

admin.site.register(ApprovalNote)
admin.site.register(JobApplicationDocument)
admin.site.register(SalaryAnnexure)
admin.site.register(SalaryComponent)
admin.site.register(SalaryAnnexureHistory)
admin.site.register(DocuSignOffer)