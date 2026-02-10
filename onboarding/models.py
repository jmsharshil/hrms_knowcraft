from django.db import models
import uuid
from jobs.models import Job,JobApplication
from accounts.models import User
# class Job(models.Model):
#     DEPARTMENT_CHOICES = [('sales',"Sales"),("marketing","Marketing"),("hr","HR"),("finance","Finance"),("engineering","Engineering")]
#     JOB_CHOICES = [("full-time","Full-time"),("part-time","Part-time"),("intern","Intern"),("contract","Contract")]

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=250)
#     company =models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
#     is_active = models.BooleanField(default=True)
#     job_openings = models.IntegerField(blank=True,null=True)
#     application_link = models.URLField(blank=True,null=True)
#     location = models.CharField(max_length=50,blank=True,null=True)
#     department = models.CharField(choices=DEPARTMENT_CHOICES,blank=True)
#     job_type = models.CharField(choices=JOB_CHOICES,default="full-time")
#     description = models.TextField(max_length=300,blank=True,default="")
#     expirience = models.CharField(blank=True,null=True)
#     salary_min =models.PositiveIntegerField(blank=True,null=True)
#     salary_max = models.PositiveIntegerField(blank=True,null=True)
#     mrf = models.ForeignKey(MRF, on_delete=models.CASCADE, related_name='jobs')

# class Candidate(models.Model):
#     CHOICES = [

#     # Submission
#     ("received", "received"),

#     # Screening & Interview
#     ("shortlisted", "Shortlisted"),
#     ("interview_pending", "Interview Pending"),
#     ("interview_done", "Interview Completed"),
#     ("interview_rejected", "Rejected After Interview"),

#     # Approval Stage
#     ("selected", "Selected by Interview Panel"),
#     ("approval_pending", "Approval Pending (Sent to Hiring Manager)"),
#     ("approved", "Approved by Hiring Manager"),
#     ("approval_rejected", "Rejected During Approval"),

#     # SALARY DOCUMENT FLOW
#     ("salary_docs_pending", "Salary Documents Pending"),
#     ("salary_docs_uploaded", "Salary Documents Uploaded"),
#     ("hr_review_docs", "HR Reviewing Salary Documents"),
#     ("hr_review_ok", "HR Review Completed"),
#     ("hr_review_rejected", "HR Rejected Salary Documents"),

#     # SALARY ANNEXURE FLOW
#     ("salary_annexure_prep", "Salary Annexure Under Preparation"),
#     ("salary_annexure_sent", "Salary Annexure Sent to HR Head"),
#     ("approved_annexure", "Salary Annexure Approved"),
#     ("rejected_annexure", "Salary Annexure Rejected"),

#     # Offer Stage
#     ("offer_pending", "Offer Preparation Pending"),
#     ("offer_sent", "Offer Sent"),
#     ("offer_accepted", "Offer Accepted"),
#     ("offer_rejected", "Offer Rejected by Candidate"),

#     # RESIGNATION FLOW
#     ("resignation_pending", "Resignation Pending (Upload Required)"),
#     ("resignation_uploaded", "Resignation Uploaded"),
#     ("resignation_review", "Resignation Under Review"),
#     ("resignation_approved", "Resignation Approved"),
#     ("resignation_rejected", "Resignation Rejected"),

#     # JOINING DOCUMENT FLOW
#     ("docs_pending", "Joining Documents Pending"),
#     ("docs_uploaded", "Joining Documents Uploaded"),
#     ("review_docs", "Document Review In Progress"),
#     ("docs_approved", "Documents Approved"),
#     ("docs_incomplete", "Documents Incomplete"),
#     ("docs_unclear", "Documents Unclear"),

#     # JOINING FLOW
#     ("joining_pending", "Joining Pending"),
#     ("joining_poned", "Joining Postponed"),
#     ("joined", "Joined"),

#     # General Rejection (fallback)
#     ("rejected", "Rejected"),
# ]

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=255)
#     email = models.EmailField(unique=True)
#     phone = models.CharField(max_length=20)
#     job =models.ForeignKey(Job, on_delete=models.CASCADE, related_name='candidates')
#     stage = models.CharField(max_length=50, choices=CHOICES, default="received")
#     is_active = models.BooleanField(default=True)
#     # designation = models.CharField(max_length=50,blank=True,null=True)
#     location = models.CharField(max_length=50,blank=True,null=True)
#     expirience = models.CharField(max_length=50,blank=True,null=True)
#     current_employer = models.CharField(max_length=50,blank=True,null=True)
#     relative_exp = models.CharField(max_length=50,blank=True,null=True)
#     match_score = models.IntegerField(blank=True,null=True)
#     current_ctc = models.IntegerField(blank=True,null=True)
#     expected_ctc = models.IntegerField(blank=True,null=True)
#     education = models.CharField(max_length=100,blank=True,null=True, default="")
#     availibility = models.CharField(blank=True,null=True)
#     notice_period = models.CharField(blank=True,null=True)
#     linkedin_link = models.URLField(blank=True,null=True)
#     portfolio_link = models.URLField(blank=True,null=True)
#     # attachments = JSONField(default=list, blank=True) # Stores file paths
#     joining_date = models.DateField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

def application_upload_path(instance, filename):
    return f"documents/{instance.job_application.id}/{filename}"

class JobApplicationDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to=application_upload_path)
    doc_type = models.CharField(max_length=100, blank=True, null=True) # e.g. "Aadhaar", "PAN"
    uploaded_at = models.DateTimeField(auto_now_add=True)

class ApprovalNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    candidate = models.ForeignKey(
        "jobs.JobApplication",
        on_delete=models.CASCADE,
        related_name="approval_notes"
    )

    manager = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="approval_notes"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_approval_notes"
    )

    # 🔹 Snapshot JSON (EMAIL = UI)
    payload = models.JSONField()

    status = models.CharField(
        max_length=30,
        default="approval_pending"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

class SalaryAnnexure(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent for Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    job_application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="salary_annexure"
    )

    prepared_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name="prepared_annexures"
    )

    reviewed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_annexures"
    )

    designation = models.CharField(max_length=255)
    effective_from = models.DateField()

    gross_monthly = models.DecimalField(max_digits=12, decimal_places=2)
    ctc_annual = models.DecimalField(max_digits=14, decimal_places=2)
    net_monthly = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    rejection_reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    revision_count = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_application} | Salary Annexure"

class SalaryComponent(models.Model):
    COMPONENT_TYPE = [
        ("earning", "Earning"),
        ("employer_contribution", "Employer Contribution"),
        ("employee_contribution", "Employee Contribution"),
    ]

    annexure = models.ForeignKey(
        SalaryAnnexure,
        on_delete=models.CASCADE,
        related_name="components"
    )

    name = models.CharField(max_length=255)
    component_type = models.CharField(max_length=30, choices=COMPONENT_TYPE)

    monthly_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    annual_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    is_statutory = models.BooleanField(default=False)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name

class SalaryAnnexureHistory(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("sent", "Sent for Approval"),
        ("revised", "Revised"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    annexure = models.ForeignKey(
        SalaryAnnexure,
        on_delete=models.CASCADE,
        related_name="history"
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    performed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True
    )

    remarks = models.TextField(blank=True, null=True)

    snapshot = models.JSONField(
        help_text="Snapshot of salary annexure at the time of action"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.annexure} - {self.action}"
