from django.db import models
import uuid
import secrets


class RecruitmentCost(models.Model):
    """Track recruitment costs per job for ROI / cost-per-hire analysis."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='recruitment_cost',
    )
    consultancy_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ads_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    referral_bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employee_package = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        null=True,
        related_name='recruitment_costs',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recruitment_costs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Cost for {self.job.job_title}"

    @property
    def total_cost(self):
        return (
            self.consultancy_fees
            + self.ads_expense
            + self.referral_bonus
            + self.employee_package
        )


class CandidateExperienceFeedback(models.Model):
    """
    Candidate Interview Experience Survey.
    Collected from candidates after rejection or offer release via a token-based link.
    Contains 7 sections: NPS, CSAT, Process Ease, Communication,
    Interviewer Quality, Recruitment Speed, and Open Feedback.
    """

    FEEDBACK_TYPE_CHOICES = [
        ('rejection', 'Rejection Feedback'),
        ('offer', 'Offer Feedback'),
    ]

    # ── Q2: Overall Satisfaction (CSAT) ──
    SATISFACTION_CHOICES = [
        (1, 'Very Dissatisfied'),
        (2, 'Dissatisfied'),
        (3, 'Satisfied'),
        (4, 'Very Satisfied'),
    ]

    # ── Q3: Process Ease ──
    PROCESS_EASE_CHOICES = [
        (1, 'Very Difficult'),
        (2, 'Difficult'),
        (3, 'Easy'),
        (4, 'Very Easy'),
    ]

    # ── Q4: Communication ──
    COMMUNICATION_CHOICES = [
        (1, 'Very Dissatisfied'),
        (2, 'Dissatisfied'),
        (3, 'Satisfied'),
        (4, 'Very Satisfied'),
    ]

    # ── Q5: Interviewer Quality ──
    INTERVIEWER_QUALITY_CHOICES = [
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]

    # ── Q6: Recruitment Speed ──
    SPEED_CHOICES = [
        (1, 'Very Slow'),
        (2, 'Slow'),
        (3, 'Acceptable'),
        (4, 'Fast'),
        (5, 'Very Fast'),
    ]

    # ── Q6b: Stage Reached ──
    STAGE_REACHED_CHOICES = [
        ('application', 'Application Stage'),
        ('hr_interview', 'HR Interview'),
        ('technical_interview', 'Technical Interview'),
        ('final_interview', 'Final Interview'),
        ('offer', 'Offer Stage'),
    ]

    # ── Identity & Link ──
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        'jobs.JobApplication',
        on_delete=models.CASCADE,
        related_name='experience_feedbacks',
    )
    feedback_token = models.CharField(max_length=64, unique=True, editable=False)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)

    # ── Q1: Net Promoter Score (NPS) – 0 to 10 ──
    nps_score = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='0 = Not at all likely, 10 = Extremely likely',
    )

    # ── Q2: Overall Satisfaction (CSAT) ──
    overall_satisfaction = models.PositiveIntegerField(
        null=True, blank=True,
        choices=SATISFACTION_CHOICES,
    )

    # ── Q3: Process Ease ──
    process_ease = models.PositiveIntegerField(
        null=True, blank=True,
        choices=PROCESS_EASE_CHOICES,
    )

    # ── Q4: Communication ──
    communication = models.PositiveIntegerField(
        null=True, blank=True,
        choices=COMMUNICATION_CHOICES,
    )

    # ── Q5: Interviewer Quality ──
    interviewer_quality = models.PositiveIntegerField(
        null=True, blank=True,
        choices=INTERVIEWER_QUALITY_CHOICES,
    )

    # ── Q6a: Recruitment Speed ──
    recruitment_speed = models.PositiveIntegerField(
        null=True, blank=True,
        choices=SPEED_CHOICES,
    )

    # ── Q6b: Stage Reached ──
    stage_reached = models.CharField(
        max_length=30, blank=True,
        choices=STAGE_REACHED_CHOICES,
    )

    # ── Q7: Open Feedback ──
    improvement_suggestion = models.TextField(
        blank=True,
        help_text='What is one thing we could improve in our recruitment process? (min 15 words)',
    )
    most_frustrating = models.TextField(
        blank=True,
        help_text='What was the most frustrating part of our recruitment process? (min 15 words)',
    )
    better_handling = models.TextField(
        blank=True,
        help_text='Was there any moment that could have been handled better? (min 15 words)',
    )

    # ── Submission Tracking ──
    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'candidate_experience_feedbacks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.application.candidate_name} - {self.feedback_type}"

    def save(self, *args, **kwargs):
        if not self.feedback_token:
            self.feedback_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    # ── NPS classification helpers ──
    @property
    def nps_category(self):
        """Promoter (9-10), Passive (7-8), or Detractor (0-6)."""
        if self.nps_score is None:
            return None
        if self.nps_score >= 9:
            return 'promoter'
        elif self.nps_score >= 7:
            return 'passive'
        return 'detractor'

    @property
    def is_csat_satisfied(self):
        """True if Satisfied or Very Satisfied (values 3, 4)."""
        return self.overall_satisfaction in (3, 4) if self.overall_satisfaction else False
