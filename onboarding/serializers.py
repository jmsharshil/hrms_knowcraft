from rest_framework import serializers
from .models import JobApplicationDocument,SalaryAnnexure,SalaryAnnexureHistory,SalaryComponent
from jobs.models import JobApplication
# class CandidateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Candidate
#         fields = [
#             'id', 'name', 'email', 'phone', 'stage', 'joining_date', 'created_at', 'updated_at','job'
#         ]
#         read_only_fields = ['id', 'created_at', 'updated_at']

#     def validate_stage(self, value):
#         valid_stages = [choice[0] for choice in Candidate.CHOICES]
#         if value not in valid_stages:
#             raise serializers.ValidationError("Invalid stage")
#         return value

class JobApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplicationDocument
        fields = "__all__"
        read_only_fields = (
            "id","job_application","salary_status",
            "joining_docs_status","resignation_status","created_at","updated_at",
        )

# class JobCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Job
#         fields = [
#             'id',
#             # 'mrf',
#             'name',
#             'company'
#         ]

    # def validate_mrf(self, value):
    #     if not MRF.objects.filter(id=value.id).exists():
    #         raise serializers.ValidationError("MRF not found.")
    #     return value

    # def create(self, validated_data):
    #     # ----- Auto generate job code -----
    #     last = Job.objects.all().count() + 1
    #     validated_data['job_code'] = f"JOB-{last:05d}"

    #     return super().create(validated_data)
class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        exclude = ("annexure",)

class SalaryAnnexureSerializer(serializers.ModelSerializer):
    candidate_id = serializers.UUIDField(write_only=True)
    components = SalaryComponentSerializer(many=True, required=False)

    class Meta:
        model = SalaryAnnexure
        fields = [
            "id","job_application","designation","effective_from","gross_monthly",
            "ctc_annual","net_monthly","notes","status","revision_count",
            "components","created_at","updated_at","candidate_id","components",
            "basic_da","basket_allowances","hra","medical_allowance","leave_travel_allowance",
            "telephone_internet_allowance","books_periodicals","uniform_allowance","driver_salary",
            "car_maintenance","meals_allowance","special_allowance","children_education_allowance",
            "conveyance_allowance","employer_pf","employer_insurance","employer_variable_component",
            "employer_gratuity","employer_esic","employer_total","employee_pf","employee_pt",
            "employee_esic","employee_total"
        ]
        read_only_fields = [
            "id",
            "job_application",
            "status",
            "reviewed_by",
            "revision_count",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        job_app_id = validated_data.pop("candidate_id")
        components = validated_data.pop("components", [])
        job_app = JobApplication.objects.filter(id=job_app_id).first()
        if not job_app:
            raise serializers.ValidationError(
                f"Job Application with id '{job_app_id}' doesn't exist."
            )
        annexure, created = SalaryAnnexure.objects.get_or_create(
            job_application=job_app,
            defaults=validated_data
        )
        for comp in components:
            SalaryComponent.objects.create(
                annexure=annexure,
                **comp
            )
        if not created:
            raise serializers.ValidationError(
                "Salary Annexure already exists for this Job Application."
            )

        return annexure

class SalaryAnnexureHistorySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SalaryAnnexureHistory
        fields = [
            "id",
            "action",
            "performed_by",
            "performed_by_name",
            "remarks",
            "snapshot",
            "created_at",
        ]
        read_only_fields = fields

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return obj.performed_by.name
        return None
