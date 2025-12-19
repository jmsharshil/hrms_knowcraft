# slots/serializers.py
from rest_framework import serializers
from .models import Interviewer,InterviewFeedback

class FreeSlotSerializer(serializers.Serializer):
    slot_id = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

class InterviewerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interviewer
        fields = ["id", "name", "email"]

class InterviewFeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewFeedback
        fields = [
            "id",
            "job_application",
            "interview_round",
            "feedback",
            "is_selected",
        ]

    def validate(self, attrs):
        """
        Prevent duplicate feedback for same round & application
        """
        if InterviewFeedback.objects.filter(
            job_application=attrs["job_application"],
            interview_round=attrs["interview_round"]
        ).exists():
            raise serializers.ValidationError(
                "Feedback for this interview round already exists."
            )
        return attrs

class InterviewFeedbackListSerializer(serializers.ModelSerializer):
    job_application_id = serializers.UUIDField(
        source="job_application.id", read_only=True
    )
    candidate_name = serializers.CharField(
        source="job_application.candidate_name", read_only=True
    )

    class Meta:
        model = InterviewFeedback
        fields = [
            "id",
            "job_application_id",
            "candidate_name",
            "interview_round",
            "feedback",
            "is_selected",
            "created_at",
        ]

class InterviewFeedbackDetailSerializer(serializers.ModelSerializer):
    job_application = serializers.SerializerMethodField()

    class Meta:
        model = InterviewFeedback
        fields = [
            "id",
            "job_application",
            "interview_round",
            "feedback",
            "is_selected",
            "created_at",
        ]

    def get_job_application(self, obj):
        return {
            "id": obj.job_application.id,
            "candidate_name": obj.job_application.candidate_name,
            "job_title": obj.job_application.job.job_title,
            "status": obj.job_application.status,
        }

class InterviewFeedbackUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewFeedback
        fields = [
            "interview_round",
            "feedback",
            "is_selected",
        ]
        read_only_fields = []  # handled manually

    def validate_interview_round(self, value):
        """
        Prevent duplicate feedback for same round in same job application
        """
        instance = self.instance  # existing feedback

        if InterviewFeedback.objects.filter(
            job_application=instance.job_application,
            interview_round=value
        ).exclude(id=instance.id).exists():
            raise serializers.ValidationError(
                "Feedback for this interview round already exists."
            )
        return value

    def update(self, instance, validated_data):
        """
        Update only allowed fields
        """
        instance.interview_round = validated_data.get(
            "interview_round", instance.interview_round
        )
        instance.feedback = validated_data.get(
            "feedback", instance.feedback
        )
        instance.is_selected = validated_data.get(
            "is_selected", instance.is_selected
        )

        instance.save()
        return instance
