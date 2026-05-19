from django.contrib import admin
from .models import CandidateBGV


@admin.register(CandidateBGV)
class CandidateBGVAdmin(admin.ModelAdmin):
    list_display = [
        "candidate",
        "status",
        "is_fresher",
        "bgv_scheduled_date",
        "ongrid_individual_id",
        "initiated_at",
        "completed_at",
    ]
    list_filter = ["status", "is_fresher"]
    search_fields = [
        "candidate__candidate_name",
        "candidate__candidate_email",
        "ongrid_individual_id",
    ]
    readonly_fields = ["id", "initiated_at"]