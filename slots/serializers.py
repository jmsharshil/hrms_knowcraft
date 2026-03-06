# slots/serializers.py
from rest_framework import serializers
from .models import Interviewer,InterviewFeedback,InterviewLocation

class FreeSlotSerializer(serializers.Serializer):
    slot_id = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

class InterviewerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interviewer
        fields = ["id", "name", "email", "company","phone"]

    def validate(self, attrs):
        request = self.context.get("request")
        company = None

        if request and request.user.is_authenticated:
            company = getattr(request.user, "company", None)
        else:
            company = attrs.get("company")

        email = attrs.get("email")

        qs = Interviewer.objects.filter(company=company, email=email)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                {"email": "This email already exists for this company."}
            )

        return attrs

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
            "designation","interview_date","interviewer_name",
            "communication_rating","technical_skill_rating","attitude_intent_rating",
            "team_handling_rating","stability_rating","problem_solving_rating",
            "analytical_thinking_rating","cultural_fit_rating",
            "competency_rating","interpersonal_skills_rating",
            "leadership_skills_rating","learning_agility_rating",
            "problem_solving_critical_thinking_decision_making_rating",
            "business_acumen_industry_understanding_rating",
            "ownership_accountibility_rating",
            "is_selected","qualification","current_organization",
            "current_organization_location","current_designation","current_location",
            "job_change_reason","notice_period","current_ctc","expected_ctc","bond",
            "work_mode","role_responsibility","strengths","areas_of_improvement",
            "strength_areas_of_improvement","goals","goals_development_plan",
            "behavioral_cultural_fit","personal_background","hometown",
            "preferred_location","behavioral",
            "communication_rating_remark","technical_skill_rating_remark",
            "attitude_intent_rating_remark","team_handling_rating_remark",
            "stability_rating_remark","problem_solving_rating_remark",
            "analytical_thinking_rating_remark","cultural_fit_rating_remark",
            "competency_rating_remark","interpersonal_skills_rating_remark",
            "leadership_skills_rating_remark","learning_agility_rating_remark",
            "problem_solving_critical_thinking_decision_making_rating_remark",
            "business_acumen_industry_understanding_rating_remark",
            "ownership_accountibility_rating_remark",
            "motivation_for_change_career_aspirations",
            "achievement_orientation_impact",
            "satbility_reliability_commitment",
            "hr_round_avg_rating","tech_round_avg_rating",
            "case_study_round_avg_rating","final_round_avg_rating",
            "management_client_round_rating"
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
            "id","job_application_id","candidate_name","interview_round","department","comments",
            "designation","interview_date","interviewer_name",
            "communication_rating","technical_skill_rating","attitude_intent_rating",
            "team_handling_rating","stability_rating","problem_solving_rating",
            "analytical_thinking_rating","cultural_fit_rating",
            "competency_rating","interpersonal_skills_rating",
            "leadership_skills_rating","learning_agility_rating",
            "problem_solving_critical_thinking_decision_making_rating",
            "business_acumen_industry_understanding_rating",
            "ownership_accountibility_rating",
            "is_selected","qualification","current_organization",
            "current_organization_location","current_designation","current_location",
            "job_change_reason","notice_period","current_ctc","expected_ctc","bond",
            "work_mode","role_responsibility","strengths","areas_of_improvement",
            "strength_areas_of_improvement","goals","goals_development_plan",
            "behavioral_cultural_fit","personal_background","hometown",
            "preferred_location","behavioral",
            "communication_rating_remark","technical_skill_rating_remark",
            "attitude_intent_rating_remark","team_handling_rating_remark",
            "stability_rating_remark","problem_solving_rating_remark",
            "analytical_thinking_rating_remark","cultural_fit_rating_remark",
            "competency_rating_remark","interpersonal_skills_rating_remark",
            "leadership_skills_rating_remark","learning_agility_rating_remark",
            "problem_solving_critical_thinking_decision_making_rating_remark",
            "business_acumen_industry_understanding_rating_remark",
            "ownership_accountibility_rating_remark",
            "motivation_for_change_career_aspirations",
            "achievement_orientation_impact",
            "satbility_reliability_commitment",
            "hr_round_avg_rating","tech_round_avg_rating",
            "case_study_round_avg_rating","final_round_avg_rating",
            "management_client_round_rating"
        ]

class InterviewFeedbackDetailSerializer(serializers.ModelSerializer):
    job_application = serializers.SerializerMethodField()

    class Meta:
        model = InterviewFeedback
        fields = [
            "id","job_application","interview_round","department","comments",
            "designation","interview_date","interviewer_name",
            "communication_rating","technical_skill_rating","attitude_intent_rating",
            "team_handling_rating","stability_rating","problem_solving_rating",
            "analytical_thinking_rating","cultural_fit_rating",
            "competency_rating","interpersonal_skills_rating",
            "leadership_skills_rating","learning_agility_rating",
            "problem_solving_critical_thinking_decision_making_rating",
            "business_acumen_industry_understanding_rating",
            "ownership_accountibility_rating",
            "is_selected","qualification","current_organization",
            "current_organization_location","current_designation","current_location",
            "job_change_reason","notice_period","current_ctc","expected_ctc","bond",
            "work_mode","role_responsibility","strengths","areas_of_improvement",
            "strength_areas_of_improvement","goals","goals_development_plan",
            "behavioral_cultural_fit","personal_background","hometown",
            "preferred_location","behavioral",
            "communication_rating_remark","technical_skill_rating_remark",
            "attitude_intent_rating_remark","team_handling_rating_remark",
            "stability_rating_remark","problem_solving_rating_remark",
            "analytical_thinking_rating_remark","cultural_fit_rating_remark",
            "competency_rating_remark","interpersonal_skills_rating_remark",
            "leadership_skills_rating_remark","learning_agility_rating_remark",
            "problem_solving_critical_thinking_decision_making_rating_remark",
            "business_acumen_industry_understanding_rating_remark",
            "ownership_accountibility_rating_remark",
            "motivation_for_change_career_aspirations",
            "achievement_orientation_impact",
            "satbility_reliability_commitment",
            "hr_round_avg_rating","tech_round_avg_rating",
            "case_study_round_avg_rating","final_round_avg_rating",
            "management_client_round_rating"
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
            "interview_round","department","comments",
            "designation","interview_date","interviewer_name",
            "communication_rating","technical_skill_rating","attitude_intent_rating",
            "team_handling_rating","stability_rating","problem_solving_rating",
            "analytical_thinking_rating","cultural_fit_rating",
            "competency_rating","interpersonal_skills_rating",
            "leadership_skills_rating","learning_agility_rating",
            "problem_solving_critical_thinking_decision_making_rating",
            "business_acumen_industry_understanding_rating",
            "ownership_accountibility_rating",
            "is_selected","qualification","current_organization",
            "current_organization_location","current_designation","current_location",
            "job_change_reason","notice_period","current_ctc","expected_ctc","bond",
            "work_mode","role_responsibility","strengths","areas_of_improvement",
            "strength_areas_of_improvement","goals","goals_development_plan",
            "behavioral_cultural_fit","personal_background","hometown",
            "preferred_location","behavioral",
            "communication_rating_remark","technical_skill_rating_remark",
            "attitude_intent_rating_remark","team_handling_rating_remark",
            "stability_rating_remark","problem_solving_rating_remark",
            "analytical_thinking_rating_remark","cultural_fit_rating_remark",
            "competency_rating_remark","interpersonal_skills_rating_remark",
            "leadership_skills_rating_remark","learning_agility_rating_remark",
            "problem_solving_critical_thinking_decision_making_rating_remark",
            "business_acumen_industry_understanding_rating_remark",
            "ownership_accountibility_rating_remark",
            "motivation_for_change_career_aspirations",
            "achievement_orientation_impact",
            "satbility_reliability_commitment",
            "hr_round_avg_rating","tech_round_avg_rating",
            "case_study_round_avg_rating","final_round_avg_rating",
            "management_client_round_rating"
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

class InterviewLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewLocation
        fields = [
            "id","name","address_line_1","address_line_2","city","state","pincode",
            "country","full_address","google_maps_link","is_active","is_default","created_at",
        ]
        read_only_fields = ["id", "full_address", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        user_company = request.user.company

        # If this location is set as default,
        # remove default from other locations of same company
        if validated_data.get("is_default"):
            InterviewLocation.objects.filter(
                company=user_company,
                is_default=True
            ).update(is_default=False)

        validated_data["company"] = user_company
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user_company = request.user.company

        # Handle default logic
        if validated_data.get("is_default"):
            InterviewLocation.objects.filter(
                company=user_company,
                is_default=True
            ).exclude(id=instance.id).update(is_default=False)

        return super().update(instance, validated_data)