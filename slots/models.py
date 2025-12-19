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
            ("round_1", "Round 1"),
            ("round_2", "Round 2"),
            ("final", "Final Round"),
        ],
        blank=True,
        null=True
    )

    feedback = models.JSONField(null=True, blank=True)
    is_selected = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_application} - {self.interview_round}"
