from rest_framework import serializers
from .models import RecruitmentCost, CandidateExperienceFeedback


class RecruitmentCostSerializer(serializers.ModelSerializer):
    """Read/write serializer for recruitment cost entries."""

    total_cost = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.job_title', read_only=True)

    class Meta:
        model = RecruitmentCost
        fields = [
            'id', 'job', 'job_title',
            'consultancy_fees', 'ads_expense',
            'referral_bonus', 'employee_package',
            'total_cost',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_cost(self, obj):
        return float(obj.total_cost)

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['company'] = user.company
        return super().create(validated_data)


class CandidateExperienceFeedbackSerializer(serializers.ModelSerializer):
    """Read serializer for admin dashboard view — all survey fields."""

    candidate_name = serializers.CharField(
        source='application.candidate_name', read_only=True
    )
    job_title = serializers.CharField(
        source='application.job.job_title', read_only=True
    )
    nps_category = serializers.CharField(read_only=True)
    overall_satisfaction_display = serializers.CharField(
        source='get_overall_satisfaction_display', read_only=True
    )
    process_ease_display = serializers.CharField(
        source='get_process_ease_display', read_only=True
    )
    communication_display = serializers.CharField(
        source='get_communication_display', read_only=True
    )
    interviewer_quality_display = serializers.CharField(
        source='get_interviewer_quality_display', read_only=True
    )
    recruitment_speed_display = serializers.CharField(
        source='get_recruitment_speed_display', read_only=True
    )
    stage_reached_display = serializers.CharField(
        source='get_stage_reached_display', read_only=True
    )

    class Meta:
        model = CandidateExperienceFeedback
        fields = [
            'id', 'application', 'candidate_name', 'job_title',
            'feedback_type',
            # Q1 - NPS
            'nps_score', 'nps_category',
            # Q2 - CSAT
            'overall_satisfaction', 'overall_satisfaction_display',
            # Q3
            'process_ease', 'process_ease_display',
            # Q4
            'communication', 'communication_display',
            # Q5
            'interviewer_quality', 'interviewer_quality_display',
            # Q6
            'recruitment_speed', 'recruitment_speed_display',
            'stage_reached', 'stage_reached_display',
            # Q7 - open feedback
            'improvement_suggestion', 'most_frustrating', 'better_handling',
            # tracking
            'is_submitted', 'submitted_at', 'created_at',
        ]


class CandidateExperienceFeedbackInfoSerializer(serializers.ModelSerializer):
    """
    Public info serializer for candidates visiting their feedback link.
    Returns only high-level info like candidate name, job title, and type.
    """

    candidate_name = serializers.CharField(
        source='application.candidate_name', read_only=True
    )
    job_title = serializers.CharField(
        source='application.job.job_title', read_only=True
    )

    class Meta:
        model = CandidateExperienceFeedback
        fields = ['candidate_name', 'job_title', 'feedback_type', 'is_submitted']


class CandidateExperienceFeedbackSubmitSerializer(serializers.Serializer):
    """
    Public serializer for candidates to submit the full survey via token.
    Validates all 7 questions according to the specified scales.
    """

    feedback_token = serializers.CharField()

    # Q1 – NPS (0-10)
    nps_score = serializers.IntegerField(min_value=0, max_value=10)

    # Q2 – Overall Satisfaction (1-4)
    overall_satisfaction = serializers.IntegerField(min_value=1, max_value=4)

    # Q3 – Process Ease (1-4)
    process_ease = serializers.IntegerField(min_value=1, max_value=4)

    # Q4 – Communication (1-4)
    communication = serializers.IntegerField(min_value=1, max_value=4)

    # Q5 – Interviewer Quality (1-5)
    interviewer_quality = serializers.IntegerField(min_value=1, max_value=5)

    # Q6a – Recruitment Speed (1-5)
    recruitment_speed = serializers.IntegerField(min_value=1, max_value=5)

    # Q6b – Stage Reached
    stage_reached = serializers.ChoiceField(
        choices=[
            'application', 'hr_interview',
            'technical_interview', 'final_interview', 'offer',
        ]
    )

    # Q7 – Open Feedback (min 15 words each)
    improvement_suggestion = serializers.CharField()
    most_frustrating = serializers.CharField()
    better_handling = serializers.CharField()

    def _validate_min_words(self, value, field_label):
        word_count = len(value.split())
        if word_count < 15:
            raise serializers.ValidationError(
                f"{field_label} must be at least 15 words (you entered {word_count})."
            )
        return value

    def validate_improvement_suggestion(self, value):
        return self._validate_min_words(value, "Improvement suggestion")

    def validate_most_frustrating(self, value):
        return self._validate_min_words(value, "Most frustrating part")

    def validate_better_handling(self, value):
        return self._validate_min_words(value, "Better handling feedback")

    def validate_feedback_token(self, value):
        try:
            fb = CandidateExperienceFeedback.objects.get(
                feedback_token=value, is_submitted=False
            )
        except CandidateExperienceFeedback.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid or already used feedback token."
            )
        self.context['feedback'] = fb
        return value

    def save(self, **kwargs):
        from django.utils import timezone

        fb = self.context['feedback']
        data = self.validated_data

        fb.nps_score = data['nps_score']
        fb.overall_satisfaction = data['overall_satisfaction']
        fb.process_ease = data['process_ease']
        fb.communication = data['communication']
        fb.interviewer_quality = data['interviewer_quality']
        fb.recruitment_speed = data['recruitment_speed']
        fb.stage_reached = data['stage_reached']
        fb.improvement_suggestion = data['improvement_suggestion']
        fb.most_frustrating = data['most_frustrating']
        fb.better_handling = data['better_handling']
        fb.is_submitted = True
        fb.submitted_at = timezone.now()
        fb.save()
        return fb
