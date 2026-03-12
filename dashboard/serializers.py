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
    """Read serializer for admin dashboard view."""

    candidate_name = serializers.CharField(
        source='application.candidate_name', read_only=True
    )
    job_title = serializers.CharField(
        source='application.job.job_title', read_only=True
    )

    class Meta:
        model = CandidateExperienceFeedback
        fields = [
            'id', 'application', 'candidate_name', 'job_title',
            'feedback_type', 'rating', 'comments',
            'is_submitted', 'submitted_at', 'created_at',
        ]


class CandidateExperienceFeedbackSubmitSerializer(serializers.Serializer):
    """Public serializer for candidates to submit feedback via token."""

    feedback_token = serializers.CharField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comments = serializers.CharField(required=False, allow_blank=True)

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
        fb.rating = self.validated_data['rating']
        fb.comments = self.validated_data.get('comments', '')
        fb.is_submitted = True
        fb.submitted_at = timezone.now()
        fb.save()
        return fb
