from openpyxl.worksheet._reader import PRINT_TAG
from jobs.models import JobApplication
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
            'id', 'candidate_name', 'job_title',
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

class CandidateExperienceFeedbackSubmitSerializer(serializers.Serializer):
    """
    Public serializer for candidates to submit the full survey via token.
    Validates all 7 questions according to the specified scales.
    """
    candidate_id = serializers.UUIDField()

    # Q1 – NPS (0-10)
    nps_score = serializers.IntegerField(min_value=0, max_value=10)

    # Q2 – Overall Satisfaction (1-4)
    overall_satisfaction = serializers.ChoiceField(choices=CandidateExperienceFeedback.SATISFACTION_CHOICES)

    # Q3 – Process Ease (1-4)
    process_ease = serializers.ChoiceField(choices=CandidateExperienceFeedback.PROCESS_EASE_CHOICES)

    # Q4 – Communication (1-4)
    communication = serializers.ChoiceField(choices=CandidateExperienceFeedback.COMMUNICATION_CHOICES)

    # Q5 – Interviewer Quality (1-5)
    interviewer_quality = serializers.ChoiceField(choices=CandidateExperienceFeedback.INTERVIEWER_QUALITY_CHOICES)

    # Q6a – Recruitment Speed (1-5)
    recruitment_speed = serializers.ChoiceField(choices=CandidateExperienceFeedback.SPEED_CHOICES)

    # Q6b – Stage Reached
    stage_reached = serializers.ChoiceField(choices=CandidateExperienceFeedback.STAGE_REACHED_CHOICES)

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


    def create(self, validated_data):
        from django.utils import timezone

        data = validated_data

        if not data.get('candidate_id'):
            raise serializers.ValidationError("Candidate ID is required")

        if not JobApplication.objects.filter(id=data['candidate_id']).exists():
            raise serializers.ValidationError("Candidate ID is invalid")
        
        # Fixed: filter by application_id instead of id
        if CandidateExperienceFeedback.objects.filter(application_id=data.get('candidate_id')).exists():
            raise serializers.ValidationError("Feedback already submitted for this candidate")
            
        feedback = CandidateExperienceFeedback.objects.create(
            application_id=data['candidate_id'],
            feedback_type='offer' if data['stage_reached'] == 'offer_accepted' else 'rejection',
            nps_score=data['nps_score'],
            overall_satisfaction=data['overall_satisfaction'],
            process_ease=data['process_ease'],
            communication=data['communication'],
            interviewer_quality=data['interviewer_quality'],
            recruitment_speed=data['recruitment_speed'],
            stage_reached=data['stage_reached'],
            improvement_suggestion=data['improvement_suggestion'],
            most_frustrating=data['most_frustrating'],
            better_handling=data['better_handling'],
            is_submitted=True,
            submitted_at=timezone.now(),
        )
        return feedback