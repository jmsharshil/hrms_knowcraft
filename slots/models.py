from django.db import models
from jobs.models import JobApplication
import uuid


class Interviewer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name

class Slot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    interviewers = models.ManyToManyField("slots.Interviewer", related_name="slots")

    class Meta:
        ordering = ["start"]

    def __str__(self):
        return f"{self.start} - {self.end} (Booked: {self.is_booked})"

class InterviewFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    job_application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="interview_feedbacks"
    )

    interview_round = models.CharField(
        max_length=50,
        choices=[
            ("hr_round", "HR Round"),
            ("technical_round_1", "Technical Round 1"),
            ("technical_round_2", "Technical Round 2"),
            ("final_round", "Final Round"),
        ],
        blank=True,
        null=True
    )

    # feedback = models.JSONField(null=True, blank=True)
    is_selected = models.BooleanField(default=True)
    department = models.CharField(null=True,blank=True)
    designation = models.CharField(null=True,blank=True)
    interview_date = models.DateField(null=True,blank=True)
    interviewer_name = models.CharField(null=True,blank=True)
    communication_rating = models.FloatField(default=0)
    technical_skill_rating = models.FloatField(default=0)
    attitude_intent_rating = models.FloatField(default=0)
    team_handling_rating = models.FloatField(default=0)
    stability_rating = models.FloatField(default=0)
    problem_solving_rating = models.FloatField(default=0)
    analytical_thinking_rating = models.FloatField(default=0)
    cultural_fit_rating = models.FloatField(default=0)
    competency_rating = models.FloatField(default=0)
    interpersonal_skills_rating = models.FloatField(default=0)
    leadership_skills_rating = models.FloatField(default=0)
    learning_agility_rating = models.FloatField(default=0)
    learning_agility_rating_remark = models.TextField(null=True,blank=True)
    problem_solving_critical_thinking_decision_making_rating = models.FloatField(default=0)
    business_acumen_industry_understanding_rating = models.FloatField(default=0)
    ownership_accountibility_rating = models.FloatField(default=0)
    ownership_accountibility_rating_remark = models.TextField(null=True,blank=True)
    problem_solving_critical_thinking_decision_making_rating_remark = models.TextField(null=True,blank=True)
    business_acumen_industry_understanding_rating_remark = models.TextField(null=True,blank=True)
    leadership_skills_rating_remark = models.TextField(null=True,blank=True)
    interpersonal_skills_rating_remark = models.TextField(null=True,blank=True)
    competency_rating_remark = models.TextField(null=True,blank=True)
    communication_rating_remark = models.TextField(null=True,blank=True)
    technical_skill_rating_remark = models.TextField(null=True,blank=True)
    attitude_intent_rating_remark = models.TextField(null=True,blank=True)
    team_handling_rating_remark = models.TextField(null=True,blank=True)
    stability_rating_remark = models.TextField(null=True,blank=True)
    problem_solving_rating_remark = models.TextField(null=True,blank=True)
    analytical_thinking_rating_remark = models.TextField(null=True,blank=True)
    cultural_fit_rating_remark = models.TextField(null=True,blank=True)
    is_selected = models.BooleanField(default=True)
    qualification = models.TextField(null=True,blank=True)
    current_organization = models.CharField(null=True,blank=True)
    current_organization_location = models.CharField(null=True,blank=True)
    job_change_reason = models.TextField(null=True,blank=True)
    notice_period = models.CharField(null=True,blank=True)
    current_ctc = models.CharField(null=True,blank=True)
    expected_ctc = models.CharField(null=True,blank=True)
    bond = models.CharField(null=True,blank=True)
    role_responsibility = models.TextField(null=True,blank=True)
    strengths = models.TextField(null=True,blank=True)
    goals = models.TextField(null=True,blank=True)
    behavioral_cultural_fit = models.TextField(null=True,blank=True)
    personal_background = models.TextField(null=True,blank=True)
    hometown = models.CharField(null=True,blank=True)
    preferred_location = models.CharField(null=True,blank=True)
    behavioral = models.TextField(default=0)
    areas_of_improvement = models.TextField(null=True,blank=True)
    strength_areas_of_improvement = models.TextField(null=True,blank=True)
    goals_development_plan = models.TextField(null=True,blank=True)
    comments = models.TextField(null=True,blank=True)
    current_designation = models.CharField(null=True,blank=True)
    current_location = models.CharField(null=True,blank=True)
    work_mode = models.CharField(null=True,blank=True)
    motivation_for_change_career_aspirations = models.TextField(null=True,blank=True)
    achievement_orientation_impact = models.TextField(null=True,blank=True)
    satbility_reliability_commitment = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_application} - {self.interview_round}"
