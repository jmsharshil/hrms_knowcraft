from django.db import models
import uuid
from slots.models import Slot
from jobs.models import JobApplication

# class Candidate(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     full_name = models.CharField(max_length=255)
#     email = models.EmailField(unique=True)

#     def __str__(self):
#         return self.full_name


class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(JobApplication, on_delete=models.CASCADE,related_name="bookings")
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name="bookings", null=True, blank=True)
    interviewer = models.ForeignKey("slots.Interviewer", on_delete=models.CASCADE)
    meeting_id = models.CharField(max_length=512, blank=True, null=True)
    meeting_link = models.TextField(blank=True, null=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    transcript = models.TextField(null=True, blank=True)
    recording_url = models.TextField(null=True, blank=True)


    def __str__(self):
        return f"{self.candidate} with {self.interviewer} at {self.start}"
