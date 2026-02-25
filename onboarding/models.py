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
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("uploaded", "Uploaded"),
        ("approved", "Approved"),
        ("unclear", "Unclear"),
        ("incomplete",'Incomplete'),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    # Salary
    salary_slip_1 = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    salary_slip_1_approved = models.BooleanField(default=False)
    salary_slip_2 = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    salary_slip_2_approved = models.BooleanField(default=False)
    salary_slip_3 = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    salary_slip_3_approved = models.BooleanField(default=False)   
    bank_statement = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    bank_statement_approved = models.BooleanField(default=False)
    # salary_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    # salary_remarks = models.TextField(blank=True, null=True)

    # Resignation
    resignation_letter = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    resignation_letter_approved = models.BooleanField(default=False)
    resignation_acceptance = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    resignation_acceptance_approved = models.BooleanField(default=False)
    # resignation_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    # resignation_remarks = models.TextField(blank=True, null=True)

    # Personal
    aadhaar = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    aadhaar_approved = models.BooleanField(default=False)
    pan = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    pan_approved = models.BooleanField(default=False)
    passport = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    passport_approved = models.BooleanField(default=False)
    photograph = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    photograph_approved = models.BooleanField(default=False)
    address_proof = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    address_proof_approved = models.BooleanField(default=False)

    # Education
    tenth_certificate = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    twelfth_certificate = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    graduation_certificate = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    post_graduation_certificate = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    additional_certificate_1 = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    additional_certificate_2 = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    additional_certificate_3 = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    tenth_certificate_approved = models.BooleanField(default=False)
    twelfth_certificate_approved = models.BooleanField(default=False)
    graduation_certificate_approved = models.BooleanField(default=False)
    post_graduation_certificate_approved = models.BooleanField(default=False)
    additional_certificate_1_approved = models.BooleanField(default=False)
    additional_certificate_2_approved = models.BooleanField(default=False)
    additional_certificate_3_approved = models.BooleanField(default=False)

    
    # Experience
    experience_letter_1 = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    experience_letter_1_approved = models.BooleanField(default=False)
    experience_letter_2 = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    experience_letter_2_approved = models.BooleanField(default=False)
    offer_letter_1 = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    offer_letter_1_approved = models.BooleanField(default=False)
    offer_letter_2 = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    offer_letter_2_approved = models.BooleanField(default=False)
    relieving_letter = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    relieving_letter_approved = models.BooleanField(default=False)
    increment_letter = models.FileField(upload_to=application_upload_path, null=True, blank=True)   
    increment_letter_approved = models.BooleanField(default=False)

    joining_docs_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    joining_docs_remarks = models.TextField(blank=True, null=True)
    salary_annexure = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    salary_annexure_approved = models.BooleanField(default=False)
    created_offer_letter = models.FileField(upload_to=application_upload_path, null=True, blank=True)
    created_offer_letter_approved = models.BooleanField(default=False)
    reupload_docuemnts = models.TextField(null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ApprovalNote(models.Model):
    STATUS_CHOICES = [
    # Submission
    ("received", "Received"),
    ("duplicate_rejected","Duplicate Rejected"),
    # Screening & Interview
    ("shortlisted", "Shortlisted"),
    ("interview_pending_1", "HR Interview Pending"),
    ("interview_done_1", "HR Interview Completed"),
    ("interview_rejected_1", "Rejected After HR Interview"),
    ("interview_next_2", "Shortlisted For Techninal Round"),
    ("interview_pending_2", "Technical Interview Pending"),
    ("interview_done_2", "Technical Interview Completed"),
    ("interview_rejected_2", "Rejected After technical Interview"),
    ("interview_next_3", "Shortlisted For Case Study Round"),
    ("interview_pending_3", "Case Study Interview Pending"),
    ("interview_done_3", "Case Study Interview Completed"),
    ("interview_rejected_3", "Rejected After Case Study Interview"),
    ("interview_next_final", "Shortlisted For Final Round"),
    ("interview_pending_final", "Final Interview Pending"),
    ("interview_done_final", "Final Round Of Interview Completed"),
    ("interview_rejected_final", "Rejected After Final Interview"),
    ("interview_next_management_client", "Shortlisted For Management / Client Interview"),
    ("interview_pending_management_client", "Management / Client Interview Pending"),
    ("interview_done_management_client", "Management / Client Interview Completed"),
    ("interview_rejected_management_client", "Rejected After Management / Client Interview"),
    # Approval Stage
    ("consolidated_result_review","Under HR Review"),
    ("selected", "Selected"),
    ("approval_pending", "Approval Pending (Sent For Approval)"),
    ("approved", "Approved by Hiring Manager"),
    ("approval_rejected", "Rejected During Approval"),
    # SALARY ANNEXURE FLOW
    ("salary_annexure_prep", "Salary Annexure Under Preparation"),
    ("salary_annexure_review", "Salary Annexure Under Review"),
    ("approved_annexure", "Salary Annexure Approved"),
    ("rejected_annexure", "Salary Annexure Rejected"),
    # Offer Stage
    ("offer_pending", "Offer Preparation Pending"),
    ("offer_sent", "Offer Drafted to Zoho Sign"),
    ("offer_accepted", "Offer Accepted"),
    ("offer_rejected", "Offer Rejected by Candidate"),
    # JOINING DOCUMENT FLOW
    ("docs_pending", "Joining Documents Pending"),
    ("docs_uploaded", "Joining Documents Uploaded"),
    ("review_docs", "Document Review In Progress"),
    ("docs_approved", "Documents Approved"),
    ("docs_incomplete", "Documents Incomplete"),
    ("docs_unclear", "Documents Unclear"),
    # JOINING FLOW
    ("joining_pending", "Joining Pending"),
    ("joining_poned", "Joining Postponed"),
    ("joined", "Joined"),
    # General Rejection (fallback)
    ("rejected", "Rejected"),
]
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
        max_length=255,
        default="approval_pending",
        choices=STATUS_CHOICES
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

    basic_da = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    basket_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    leave_travel_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    telephone_internet_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    books_periodicals = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    uniform_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    driver_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    car_maintenance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    meals_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    children_education_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    conveyance_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    employer_pf = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employer_insurance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employer_variable_component = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employer_gratuity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employer_esic = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    employer_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    employee_pf = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employee_pt = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employee_esic = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    employee_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

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

class OfferDocument(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("viewed", "Viewed"),
        ("signed", "Signed"),
        ("completed", "Completed"),
        ("declined", "Declined"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE)
    zoho_request_id = models.CharField(max_length=255)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="draft"
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    signed_file = models.FileField(upload_to="signed_docs/", null=True, blank=True)
    raw_response = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "offer_documents"
        ordering = ["-created_at"]

    def __str__(self):
        return self.application.candidate_name
