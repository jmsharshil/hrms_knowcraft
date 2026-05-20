# bgv/serializers.py

from rest_framework import serializers
from .models import CandidateBGV


class CandidateBGVSerializer(serializers.ModelSerializer):

    candidate_name = serializers.CharField(
        source="candidate.candidate_name",
        read_only=True,
    )
    candidate_email = serializers.EmailField(
        source="candidate.candidate_email",
        read_only=True,
    )
    candidate_phone = serializers.CharField(
        source="candidate.candidate_phone",
        read_only=True,
    )
    job_title = serializers.CharField(
        source="candidate.job.job_title",
        read_only=True,
    )
    experience_years = serializers.DecimalField(
        source="candidate.experience_years",
        read_only=True,
        max_digits=4,
        decimal_places=1,
    )
    joining_date = serializers.DateField(
        source="candidate.joining_date",
        read_only=True,
    )

    class Meta:
        model = CandidateBGV
        fields = [
            "id",
            "candidate",
            "candidate_name",
            "candidate_email",
            "candidate_phone",
            "job_title",
            "experience_years",
            "joining_date",
            "ongrid_individual_id",
            "status",
            "is_fresher",
            "bgv_scheduled_date",
            "report_url",
            "callback_payload",
            "initiated_at",
            "completed_at",
            "remarks",
        ]
        read_only_fields = [
            "id",
            "ongrid_individual_id",
            "status",
            "is_fresher",
            "bgv_scheduled_date",
            "report_url",
            "callback_payload",
            "initiated_at",
            "completed_at",
        ]