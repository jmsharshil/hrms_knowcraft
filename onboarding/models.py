from django.db import models
from django.contrib.postgres.fields import JSONField
from datetime import datetime
import uuid
from accounts.models import Company

class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=250)
    company =models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    is_active = models.BooleanField(default=True)
    job_openings = models.IntegerField(blank=True,null=True)
    application_link = models.URLField(blank=True,null=True)

class Candidate(models.Model):
    CHOICES = [

    # Submission
    ("applied", "Applied"),

    # Screening & Interview
    ("shortlisted", "Shortlisted"),
    ("interview_pending", "Interview Pending"),
    ("interview_done", "Interview Completed"),
    ("interview_rejected", "Rejected After Interview"),

    # Approval Stage
    ("selected", "Selected by Interview Panel"),
    ("approval_pending", "Approval Pending (Sent to Hiring Manager)"),
    ("approved", "Approved by Hiring Manager"),
    ("approval_rejected", "Rejected During Approval"),

    # Offer Stage
    ("offer_pending", "Offer Preparation Pending"),
    ("offer_sent", "Offer Sent"),
    ("offer_accepted", "Offer Accepted"),
    ("offer_rejected", "Offer Rejected by Candidate"),

    # Documentation & Joining
    ("docs_pending", "Documents Pending"),
    ("docs_received", "Documents Received"),
    ("joining_pending", "Joining Pending"),
    ("joined", "Joined"),

    # General Rejection (fallback)
    ("rejected", "Rejected"),
]

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    job =models.ForeignKey(Job, on_delete=models.CASCADE, related_name='candidates')
    stage = models.CharField(max_length=50, choices=CHOICES, default="applied")
    is_active = models.BooleanField(default=True)
    designation = models.CharField(max_length=50,blank=True)
    location = models.CharField(max_length=50,blank=True)
    expirience = models.CharField(max_length=50,blank=True)
    # attachments = JSONField(default=list, blank=True) # Stores file paths
    joining_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

def candidate_upload_path(instance, filename):
    return f"candidates/{instance.candidate.id}/{filename}"

class CandidateDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to=candidate_upload_path)
    doc_type = models.CharField(max_length=100, blank=True, null=True) # e.g. "Aadhaar", "PAN"
    uploaded_at = models.DateTimeField(auto_now_add=True)