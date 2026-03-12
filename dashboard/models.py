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
    """Feedback collected from candidates after rejection or offer release."""

    FEEDBACK_TYPE_CHOICES = [
        ('rejection', 'Rejection Feedback'),
        ('offer', 'Offer Feedback'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        'jobs.JobApplication',
        on_delete=models.CASCADE,
        related_name='experience_feedbacks',
    )
    feedback_token = models.CharField(max_length=64, unique=True, editable=False)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)

    # Candidate fills these
    rating = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Rating out of 5',
    )
    comments = models.TextField(blank=True)
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
