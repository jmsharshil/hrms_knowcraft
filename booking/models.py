from django.db import models
from django.utils import timezone
import uuid
from slots.models import Slot
from jobs.models import JobApplication

class Booking(models.Model):
    INTERVIEW_TYPE_CHOICES = (
        ("online", "Online"),
        ("in_person", "In Person"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(JobApplication, on_delete=models.CASCADE,related_name="bookings")
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPE_CHOICES, default="online")
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name="bookings", null=True, blank=True)
    interviewer = models.ForeignKey("slots.Interviewer", on_delete=models.CASCADE)
    meeting_id = models.CharField(max_length=512, blank=True, null=True)
    meeting_link = models.TextField(blank=True, null=True)
    location = models.ForeignKey("slots.InterviewLocation", on_delete=models.CASCADE,blank=True, null=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    transcript = models.TextField(null=True, blank=True)
    recording_url = models.TextField(null=True, blank=True)
    attendees = models.ManyToManyField("slots.Interviewer", related_name="attendees",blank=True)


    def __str__(self):
        return f"{self.candidate} with {self.interviewer} at {self.start}"

    class Meta:
        indexes = [
            models.Index(fields=["start"]),
            models.Index(fields=["interviewer"]),
            models.Index(fields=["location"]),
            models.Index(fields=["interview_type"]),
        ]

class GraphEventLog(models.Model):
    event_id = models.CharField(max_length=255)
    change_type = models.CharField(max_length=50)
    subscription_id = models.CharField(max_length=255)
    resource = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("event_id", "change_type", "subscription_id")

class SystemLock(models.Model):
    key = models.CharField(max_length=100, unique=True)
    locked_at = models.DateTimeField(default=timezone.now)