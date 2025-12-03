from rest_framework import serializers
from .models import JobApplicationDocument

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
        fields = ["id", "file", "doc_type", "uploaded_at"]

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