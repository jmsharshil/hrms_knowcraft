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

    interview_date = serializers.DateField(
        format="%d/%m/%Y",
        input_formats=["%d/%m/%Y","%d-%m-%Y","%Y-%m-%d","%Y/%m/%d"],
        required=False,
        allow_null=True
    )

    class Meta:
        model = InterviewFeedback
        fields = [
            "id","job_application","interview_round","department","comments",
            "designation","interview_date","interviewer_name","communication_rating",
            "technical_skill_rating","attitude_intent_rating","team_handling_rating",
            "stability_rating","problem_solving_rating","analytical_thinking_rating",
            "cultural_fit_rating","is_selected","qualification","current_organization",
            "job_change_reason","notice_period","current_ctc","expected_ctc","bond",
            "role_responsibility","strengths","goals","behavioral_cultural_fit",
            "personal_background","hometown","preferred_location","behavioral",
            "communication_rating_remark","technical_skill_rating_remark",
            "attitude_intent_rating_remark","team_handling_rating_remark",
            "stability_rating_remark","problem_solving_rating_remark",
            "analytical_thinking_rating_remark","cultural_fit_rating_remark"
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
            "id","job_application_id","candidate_name","interview_round","department",
            "designation","interview_date","interviewer_name","communication_rating",
            "technical_skill_rating","attitude_intent_rating","team_handling_rating",
            "stability_rating","problem_solving_rating","analytical_thinking_rating",
            "cultural_fit_rating","is_selected","qualification","current_organization",
            "job_change_reason","notice_period","current_ctc","expected_ctc","bond",
            "role_responsibility","strengths","goals","behavioral_cultural_fit",
            "personal_background","hometown","preferred_location","behavioral",
            "comments","created_at","current_organization_location",
            "communication_rating_remark","technical_skill_rating_remark",
            "attitude_intent_rating_remark","team_handling_rating_remark",
            "stability_rating_remark","problem_solving_rating_remark",
            "analytical_thinking_rating_remark","cultural_fit_rating_remark"
        ]

class InterviewFeedbackDetailSerializer(serializers.ModelSerializer):
    job_application = serializers.SerializerMethodField()

    class Meta:
        model = InterviewFeedback
        fields = [
            "id","job_application","interview_round","department",
            "designation","interview_date","interviewer_name","communication_rating",
            "technical_skill_rating","attitude_intent_rating","team_handling_rating",
            "stability_rating","problem_solving_rating","analytical_thinking_rating",
            "cultural_fit_rating","is_selected","qualification","current_organization",
            "job_change_reason","notice_period","current_ctc","expected_ctc","bond",
            "role_responsibility","strengths","goals","behavioral_cultural_fit",
            "personal_background","hometown","preferred_location","behavioral",
            "comments","created_at","current_organization_location",
            "communication_rating_remark","technical_skill_rating_remark",
            "attitude_intent_rating_remark","team_handling_rating_remark",
            "stability_rating_remark","problem_solving_rating_remark",
            "analytical_thinking_rating_remark","cultural_fit_rating_remark"
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
            "interview_round","department","designation","interview_date",
            "interviewer_name","communication_rating","technical_skill_rating",
            "attitude_intent_rating","team_handling_rating","stability_rating",
            "problem_solving_rating","analytical_thinking_rating","cultural_fit_rating",
            "is_selected","qualification","current_organization","job_change_reason",
            "notice_period","current_ctc","expected_ctc","bond","role_responsibility",
            "strengths","goals","behavioral_cultural_fit","personal_background",
            "hometown","preferred_location","behavioral","comments",
            "communication_rating_remark","technical_skill_rating_remark",
            "attitude_intent_rating_remark","team_handling_rating_remark",
            "stability_rating_remark","problem_solving_rating_remark",
            "analytical_thinking_rating_remark","cultural_fit_rating_remark"
        ]

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
        for field in self.Meta.fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
