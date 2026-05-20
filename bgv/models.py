# bgv/models.py

import uuid
from django.db import models


class CandidateBGV(models.Model):

    STATUS_CHOICES = [
        ("pending_schedule", "Pending Schedule"),
        ("initiated", "Initiated"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("insufficient", "Insufficient"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    candidate = models.OneToOneField(
        "jobs.JobApplication",
        on_delete=models.CASCADE,
        related_name="bgv"
    )

    ongrid_individual_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="pending_schedule"
    )

    report_url = models.URLField(null=True, blank=True)

    callback_payload = models.JSONField(default=dict, blank=True)

    initiated_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    remarks = models.TextField(null=True, blank=True)

    # Scheduling fields for experienced candidates
    bgv_scheduled_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when BGV should be triggered (15 days before joining for experienced candidates)"
    )

    is_fresher = models.BooleanField(
        default=True,
        help_text="True if candidate has < 1 year experience"
    )

    def __str__(self):
        return f"{self.candidate.candidate_name} - {self.status}"