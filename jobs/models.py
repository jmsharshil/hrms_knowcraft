from django.db import models
from django.utils import timezone
import uuid
import secrets
from django.db.models import Q, UniqueConstraint
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files import File

FRONTEND_URL = getattr(settings,"FRONTEND_URL")

class Job(models.Model):
    """Job model created from approved MRFs"""
    
    JOB_STATUS_CHOICES = [
        ('open', 'Open'),
        ('assigned_to_consultancy', 'Assigned to Consultancy'),
        ('assigned_to_internal_hr', 'Assigned to Internal HR'),
        ('assigned_to_both',"Assigned to Both"),
        # ('in_progress', 'In Progress'),
        ('filled', 'Position Filled'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    JOB_TYPE_CHOICES =[
        ('work_from_office','Work From Office'),
        ('work_from_home',"Work From Home"),
        ('hybrid','Hybrid')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to MRF
    mrf = models.OneToOneField(
        'mrf.MRF',
        on_delete=models.CASCADE,
        related_name='job',
        help_text='Related MRF that created this job'
    )
    
    # Job Details (copied from MRF for easy access)
    job_title = models.CharField(max_length=255)
    department = models.ForeignKey(
        'mrf.Department',
        on_delete=models.SET_NULL,
        null=True,
        related_name='jobs'
    )
    designation = models.ForeignKey(
        'mrf.Designation',
        on_delete=models.SET_NULL,
        null=True,
        related_name='jobs'
    )
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=50,choices=JOB_TYPE_CHOICES,default="work_from_office")
    no_of_positions = models.PositiveIntegerField(default=1)
    positions_filled = models.PositiveIntegerField(default=0)
    
    # Job Requirements
    key_responsibility = models.TextField()
    required_qualifications = models.TextField()
    experience_range = models.CharField(max_length=50)
    skills_competencies = models.TextField()
    technical_skills = models.TextField()
    salary_range = models.CharField(max_length=100)
    
    # Job Status
    status = models.CharField(
        max_length=50,
        choices=JOB_STATUS_CHOICES,
        default='open'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    # Assignment Details
    assigned_to_consultancy = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_jobs',
        limit_choices_to={'role': 'consultancy'}
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs_assigned'
    )
    assigned_to_internal_hr = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_internal_jobs',
        limit_choices_to={'role__in': ['hr', 'hr_manager']}  # adjust roles if different in your app
    )
    assigned_internal_at = models.DateTimeField(null=True, blank=True)
    assigned_internal_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs_assigned_internal'
    )
    # Closure Details
    closed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs_closed'
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closure_notes = models.TextField(blank=True)
    
    # Tracking
    posted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='jobs_posted'
    )
    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='jobs',
        null=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Deadline
    expected_closure_date = models.DateField(null=True, blank=True)
    
    # Visibility
    is_active = models.BooleanField(default=True)
    visible_to_consultancy = models.BooleanField(default=False)
    
    # Job Description (optional rich text for public posting)
    job_description = models.TextField(blank=True, help_text='Detailed job description for public posting')
    
    class Meta:
        db_table = 'jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['department']),
            models.Index(fields=['assigned_to_consultancy']),
            models.Index(fields=['created_at']),
            models.Index(fields=['assigned_to_internal_hr']),
        ]
    
    def __str__(self):
        return f"{self.job_title} - {self.department.name if self.department else 'N/A'}"
    
    def can_be_assigned_to_consultancy(self):
        """Check if job can be assigned to consultancy"""
        return self.status == 'open' and self.is_active
    
    def can_be_assigned_to_internal_hr(self):
        """Check if job can be assigned to internal HR"""
        return self.status == 'open' and self.is_active
    
    def remaining_positions(self):
        """Get remaining positions to fill"""
        return self.no_of_positions - self.positions_filled


class JobApplicationLink(models.Model):
    """Unique application links for different platforms"""
    
    PLATFORM_CHOICES = [
        ('linkedin', 'LinkedIn'),
        ('naukri', 'Naukri'),
        ('indeed', 'Indeed'),
        ('website', 'Company Website'),
        ('career_page', 'Career Page'),
        ('referral', 'Employee Referral'),
        ('email', 'Email'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='application_links'
    )
    
    # Platform Details
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    platform_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Custom platform name if "other" is selected'
    )
    
    # Unique Link
    unique_token = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text='Unique token for the application link'
    )

    #qr code
    qr_code = models.FileField(upload_to='job_qrcodes/', blank=True, null=True)
    
    # Link Details
    title = models.CharField(max_length=255, help_text='Title for this link')
    description = models.TextField(blank=True, help_text='Description or notes about this link')
    
    # Tracking
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_links'
    )
    
    # Statistics
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Link expiration date (optional)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_application_links'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['unique_token']),
            models.Index(fields=['job', 'platform']),
        ]
    
    def __str__(self):
        return f"{self.job.job_title} - {self.get_platform_display()}"
    
    def save(self, *args, **kwargs):
        if not self.unique_token:
            # Generate unique token
            self.unique_token = secrets.token_urlsafe(32)
        if not self.qr_code:
            # Generate the URL from your existing method
            url_to_encode = self.get_application_url()
            
            # Generate QR Image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url_to_encode)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to memory buffer
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            
            # Save to FileField (This triggers the upload to Azure Blob Storage)
            file_name = f'qr_{self.platform}_{self.unique_token[:8]}.png'
            self.qr_code.save(file_name, File(buffer), save=False)
            buffer.close()
        super().save(*args, **kwargs)
    
    def get_application_url(self):
        """Get the full application URL"""
        from django.conf import settings
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        # return f"{base_url}/apply/{self.unique_token}"
        if self.platform == 'referral':
        # If it's a referral, add 'referral' in the URL path
            return f"{FRONTEND_URL}/referral/{self.unique_token}"
    
    # For other platforms, keep the URL format the same
        return f"{FRONTEND_URL}/apply/{self.unique_token}"
        # return f"https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net/apply/{self.unique_token}"
    
    def is_expired(self):
        """Check if link is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def increment_views(self):
        """Increment views count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_applications(self):
        """Increment applications count"""
        self.applications_count += 1
        self.save(update_fields=['applications_count'])


class JobApplication(models.Model):
    """Track applications/candidates for jobs"""
    
    # STATUS_CHOICES = [
    #     ('received', 'Received'),
    #     ('screening', 'Under Screening'),
    #     ('shortlisted', 'Shortlisted'),
    #     ('interview_scheduled', 'Interview Scheduled'),
    #     ('interviewed', 'Interviewed'),
    #     ('selected', 'Selected'),
    #     ('rejected', 'Rejected'),
    #     ('offer_sent', 'Offer Sent'),
    #     ('offer_accepted', 'Offer Accepted'),
    #     ('offer_declined', 'Offer Declined'),
    #     ('joined', 'Joined'),
    #     ('withdrawn', 'Withdrawn'),
    # ]

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

    
    SOURCE_CHOICES = [
        ('internal_hr', 'Internal HR'),
        ('consultancy', 'Consultancy'),
        ('application_link', 'Application Link'),
        ('direct', 'Direct Application'),
        ('referral', 'Employee Referral'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    
    # Application Link (if applied through link)
    application_link = models.ForeignKey(
        JobApplicationLink,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
        help_text='Link through which candidate applied'
    )
    
    # Resume (REQUIRED - direct upload)
    resume = models.FileField(upload_to='resumes/', help_text='Candidate resume in any format')
    original_filename = models.CharField(max_length=255, blank=True, help_text='Original file name')
    file_size = models.PositiveIntegerField(default=0, help_text='File size in bytes')
    
    # Candidate Details (OPTIONAL - can be filled by HR later)
    candidate_name = models.CharField(max_length=255, blank=True)
    candidate_email = models.EmailField(blank=True, null=True)
    candidate_phone = models.CharField(max_length=20, blank=True)
    cover_letter = models.TextField(blank=True)

    location = models.CharField(max_length=255,blank=True,null=True)
    availibility = models.CharField(blank=True,null=True)
    current_employer = models.CharField(max_length=50,blank=True,null=True)
    skill = models.JSONField(blank=True,null=True,default=list)
    education = models.JSONField(blank=True,null=True,default=list)
    
    # Source
    submitted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications_submitted'
    )
    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default='direct'
    )
    
    # Status
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='received'
    )
    
    # Additional Info
    notes = models.TextField(blank=True)
    experience_years = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )
    relevant_experience_years = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )
    current_ctc = models.CharField(max_length=50, blank=True,null=True)
    expected_ctc = models.CharField(max_length=50, blank=True,null=True)
    notice_period = models.CharField(max_length=50, blank=True,null=True)
    
    # LinkedIn Profile
    linkedin_url = models.URLField(blank=True, max_length=500,null=True)
    
    # Portfolio/GitHub
    portfolio_url = models.URLField(blank=True, max_length=500,null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Rating (optional)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Rating out of 5'
    )
    
    #AI Parsed Score
    match_score = models.DecimalField(blank=True,null=True,max_digits=5,decimal_places=2,help_text="Score out of 0 to 100")
    resume_report = models.FileField(blank=True,null=True,upload_to='reports/', help_text='Candidate resume report.')

    joining_date = models.DateField(null=True, blank=True) 
    is_active = models.BooleanField(default=True) #Status of Application (for archiving)

    is_duplicate = models.BooleanField(default=False)
    is_shortlisted = models.BooleanField(default=False)
    is_selected = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)

    slot_link = models.URLField(null=True,blank=True)
    candidate_history = models.JSONField(null=True,blank=True,default=list)

    consolidated_feedback_avg = models.FloatField(default=0)
    rejection_reason = models.TextField(null=True,blank=True)
    
    referral_name = models.CharField(null=True,blank=True)
    referral_email = models.CharField(null=True,blank=True)
    referral_phone = models.CharField(null=True,blank=True)
    referral_emp_code = models.CharField(null=True,blank=True)
    referral_designation = models.CharField(null=True,blank=True)
    referral_department = models.CharField(null=True,blank=True)

    #Interview Details
    interview_scheduled_at = models.DateTimeField(null=True,blank=True)
    interviewer_name = models.CharField(null=True,blank=True)
    interview_link = models.TextField(null=True,blank=True)
    feedback_link = models.TextField(null=True,blank=True)
    
    class Meta:
        db_table = 'job_applications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['source']),
            models.Index(fields=['application_link']),
        ]
    
    def __str__(self):
        return f"{self.candidate_name} - {self.job.job_title}"
    
    def get_platform_name(self):
        """Get the platform name from application link"""
        if self.application_link:
            return self.application_link.get_platform_display()
        return self.get_source_display()


class JobAssignmentHistory(models.Model):
    """Track job assignment and status history"""
    
    ACTION_CHOICES = [
        ('created', 'Job Created'),
        ('assigned', 'Assigned to Consultancy'),
        ('reassigned', 'Reassigned to Another Consultancy'),
        ('unassigned', 'Unassigned from Consultancy'),
        ('assigned_internal', 'Assigned to Internal HR'),            # NEW
        ('reassigned_internal', 'Reassigned to Another Internal HR'),# NEW (optional)
        ('status_changed', 'Status Changed'),
        ('priority_changed', 'Priority Changed'),
        ('closed', 'Job Closed'),
        ('reopened', 'Job Reopened'),
        ('cancelled', 'Job Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    consultancy = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_assignments'
    )
    performed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='job_actions_performed'
    )
    notes = models.TextField(blank=True)
    
    # Store old and new values for changes
    old_value = models.CharField(max_length=255, blank=True)
    new_value = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'job_assignment_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.job.job_title} - {self.action} at {self.created_at}"
    
class ReferralApplication(models.Model):
    """Track applications through referral""" 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Resume (REQUIRED - direct upload)
    resume = models.FileField(upload_to='referral_resumes/', help_text='Referral resume in any format')
    original_filename = models.CharField(max_length=255, blank=True, help_text='Original file name')
    file_size = models.PositiveIntegerField(default=0, help_text='File size in bytes')
    
    # Additional Info
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #Referrer Info    
    referral_name = models.CharField(null=True,blank=True)
    referral_email = models.CharField(null=True,blank=True)
    referral_phone = models.CharField(null=True,blank=True)
    referral_emp_code = models.CharField(null=True,blank=True)
    referral_designation = models.CharField(null=True,blank=True)
    referral_department = models.CharField(null=True,blank=True)
    position_title = models.CharField(null=True,blank=True)
    
    class Meta:
        db_table = 'referral_applications'
        ordering = ['-created_at']
     