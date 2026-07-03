from django.db import models
from django.utils import timezone
from jobs.models import JobApplication
from accounts.models import Company
import uuid


class Interviewer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(null=True,blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    subscription_id = models.CharField(max_length=255, null=True, blank=True)
    subscription_expiry = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Soft delete flag for interviewer")

    class Meta:
        ordering = ['email']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'email'],
                name='uniq_interviewer_email_per_company'
            ),
        ]

    def __str__(self):
        return self.name

    def soft_delete(self):
        """Soft delete interviewer (sets is_active=False). Update related MRFs/feedback if needed via signals or views."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

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
            ("technical_round", "Technical Round"),
            ("case_study_round", "Case Study Round"),
            ("final_round", "Final Round"),
            ("management_client_round", "Management / Client Round")
        ],
        blank=True,
        null=True
    )

    # feedback = models.JSONField(null=True, blank=True)
    is_selected = models.CharField(blank=True,null=True,default='reject',choices=[('hire','Hire'),('strong_hire','Strong Hire'),('reject','Reject')])
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
    hr_round_avg_rating = models.FloatField(default=0)
    tech_round_avg_rating = models.FloatField(default=0)
    case_study_round_avg_rating = models.FloatField(default=0)
    final_round_avg_rating = models.FloatField(default=0)
    management_client_round_rating = models.FloatField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.job_application} - {self.interview_round}"
    
    def get_round_avg(self):
        round_field_map = {
            "hr_round": self.hr_round_avg_rating,
            "technical_round": self.tech_round_avg_rating,
            "case_study_round": self.case_study_round_avg_rating,
            "final_round": self.final_round_avg_rating,
            "management_client_round": self.management_client_round_rating,
        }

        avg = round_field_map.get(self.interview_round)
        return avg if avg is not None else 0

import urllib.parse

class InterviewLocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Human-readable name for the location (e.g., Headquarters, Client Site)
    name = models.CharField(max_length=255,default='Knowcraft')

    # Address components
    address_line_1 = models.CharField(max_length=255,default='14th Floor, 1410, West Wing,Venus Stratum, Jhansi Ki Rani,B/H GSRTC Bus Stop, Nehrunagar')
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100,default='Ahmedabad')
    state = models.CharField(max_length=100,default='Gujarat')
    pincode = models.CharField(max_length=20,default='380015')
    country = models.CharField(max_length=100, default="India")

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)

    # Full address for emails/notifications
    full_address = models.TextField(blank=True, null=True)

    # Google Maps link for navigation
    google_maps_link = models.URLField(blank=True, null=True)

    # Link to company
    company = models.ForeignKey(
        "accounts.Company",
        on_delete=models.CASCADE,
        related_name="interview_locations",
        null=True,blank=True
    )

    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        """Generate full_address and google_maps_link automatically on save."""
        # Build full address
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.pincode,
            self.country
        ]
        self.full_address = ", ".join([part for part in address_parts if part])

        # # Generate Google Maps link
        # if self.place_id:
        #     self.google_maps_link = (
        #         f"https://www.google.com/maps/place/?q=place_id:{self.place_id}"
        #     )
        # elif self.latitude is not None and self.longitude is not None:
        #     self.google_maps_link = (
        #         f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        #     )
        # else:
        #     query = urllib.parse.quote_plus(self.full_address)
        #     self.google_maps_link = f"https://www.google.com/maps/search/?api=1&query={query}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.city}"