from django.db import models,transaction
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
        ('on_hold', 'On Hold'),
        ('joining_pending', 'Joining Pending'),
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
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    # Deadline
    expected_closure_date = models.DateField(null=True, blank=True)
    
    # Visibility
    is_active = models.BooleanField(default=True)
    visible_to_consultancy = models.BooleanField(default=False)

    # Private Job fields (inherited from Private MRF)
    is_private = models.BooleanField(
        default=False,
        help_text="If True, this job is only visible to authorized users"
    )
    selected_viewers = models.ManyToManyField(
        'accounts.User',
        blank=True,
        related_name='viewable_private_jobs',
        help_text="Users who can view this private job"
    )
    
    # Job Description (optional rich text for public posting)
    job_description = models.TextField(blank=True, help_text='Detailed job description for public posting')

    assigned_consultancies = models.ManyToManyField(
        'accounts.User',
        blank=True,
        null=True,
        related_name='consultancy_jobs',
        limit_choices_to={'role': 'consultancy'}
    )

    assigned_internal_hrs = models.ManyToManyField(
        'accounts.User',
        blank=True,
        null=True,
        related_name='internal_hr_jobs',
        limit_choices_to={'role__in': ['hr', 'hr_manager','admin']}
    )

    # NEW: Fields for Hold Tracking
    previous_status = models.CharField(
        max_length=50, 
        choices=[(choice[0], choice[1]) for choice in JOB_STATUS_CHOICES if choice[0] != 'on_hold'],  # Exclude 'on_hold'
        blank=True, 
        null=True, 
        help_text="Status before being put on hold (for restoration)"
    )
    held_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when put on hold")
    hold_reason = models.TextField(blank=True, help_text="Reason for holding the job")
    
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
    
    def save(self, *args, **kwargs):
        from datetime import datetime, time
        from django.utils import timezone
        
        # Check if expected_closure_date is changing
        old_closure_date = None
        if self.pk:
            try:
                old_closure_date = Job.objects.get(pk=self.pk).expected_closure_date
            except Job.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Sync related application links if date changed
        if self.expected_closure_date != old_closure_date:
            expiry_dt = None
            if self.expected_closure_date:
                expiry_dt = timezone.make_aware(datetime.combine(self.expected_closure_date, time.max))
            
            # Use update() to propagate to all related links efficiently
            self.application_links.update(expires_at=expiry_dt)

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

    def is_on_hold(self):
        return self.status == 'on_hold'
    
    def soft_delete(self):
        """Soft delete this Job and cascade to related records (MRF, applications, links).
        Consistent with dashboard/analytics filters that use is_active=True.
        """
        with transaction.atomic():
            self.is_active = False
            self.save(update_fields=['is_active', 'updated_at'])
            
            # Deactivate related application links
            self.application_links.filter(is_active=True).update(is_active=False)
            
            # Deactivate related JobApplications and Applications
            # self.applications.filter(is_active=True).update(is_active=False)
            # Also handle platform applications if linked
            # Application.objects.filter(job=self, is_active=True).update(is_active=False)
            
            # Sync with MRF if exists
            if hasattr(self, 'mrf') and self.mrf and self.mrf.is_active:
                self.mrf.soft_delete()
            
            # Log the soft delete
            try:
                JobAssignmentHistory.objects.create(
                    job=self,
                    action='deleted',
                    performed_by=None,  # system action
                    notes='Soft deleted via API'
                )
            except Exception:
                pass  # non-critical
    
    # @classmethod
    # @transaction.atomic
    # def close_expired_jobs(cls):
    #     """
    #     Close all jobs where expected_closure_date <= today and status != 'closed'.
    #     Updates previous_status, closure_notes, saves job.
    #     Syncs expected_closure_date to applications and sets their status='expired'.
    #     Logs to JobAssignmentHistory if available.
    #     Returns (closed_count, app_updated_count)
    #     """
    #     today = timezone.now().date()
    #     expired_jobs = cls.objects.filter(
    #         expected_closure_date__lte=today,
    #         status__in=['open', 'assigned_to_both', 'assigned_to_internal_hr', 'assigned_to_consultancy'],
    #         expected_closure_date__isnull=False
    #     )

    #     closed_count = 0
    #     app_updated_count = 0

    #     for job in expired_jobs:
    #         old_status = job.status

    #         # Close job
    #         job.previous_status = old_status
    #         job.closure_notes = 'expiry'
    #         job.status = 'closed'
    #         job.save()

    #         # Log in history (assuming JobAssignmentHistory exists; skip if not)
    #         try:
    #             from .models import JobAssignmentHistory  # Avoid circular import
    #             JobAssignmentHistory.objects.create(
    #                 job=job,
    #                 old_status=old_status,
    #                 new_status='closed',
    #                 changed_by=None  # Or set to a system user
    #             )
    #         except (ImportError, Exception) as e:
    #             print(e)
    #             pass  # Skip logging if model doesn't exist or error

    #         closed_count += 1  # Moved inside loop, after processing

    #     # Optional: Print/log summary (visible in server logs)
    #     print(f'Expiry check: Closed {closed_count} expired jobs and updated {app_updated_count} applications.')
    #     return closed_count, app_updated_count

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
        ('direct',"Direct Application"),
        ('campus_drive',"Campus Drive"),
        ('internal_hr','Internal HR'),
        ('consultancy','Consultancy'),
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
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
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
        from datetime import datetime, time
        from django.utils import timezone

        if not self.unique_token:
            # Generate unique token
            self.unique_token = secrets.token_urlsafe(32)
        
        # Default expires_at to job's expected_closure_date if not set
        if not self.expires_at and self.job and self.job.expected_closure_date:
            self.expires_at = timezone.make_aware(datetime.combine(self.job.expected_closure_date, time.max))
            
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

    def soft_delete(self):
        """Soft delete this job application link (sets is_active=False).
        Cascades to related applications in views.
        """
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])


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
        ('career_page', 'Career Page'),
        ('linkedin', 'LinkedIn'),
        ('naukri', 'Naukri'),
        ('indeed', 'Indeed'),
        ("campus_drive","Campus Drive")
    ]
    
    INTERVIEW_CHOICES=[
            ("hr_round", "HR Round"),
            ("technical_round", "Technical Round"),
            ("case_study_round", "Case Study Round"),
            ("final_round", "Final Round"),
            ("management_client_round", "Management / Client Round")
        ]
    
    BGV_STATUS_CHOICES = [
    ("pending_schedule", "Pending Schedule"),

    # Active states
    ("initiated", "BGV Initiated"),
    ("pending", "Pending Verification"),
    ("in_progress", "BGV In Progress"),
    ("under_review", "Under Review"),
    ("insufficiency_raised", "Insufficiency Raised"),
    ("data_insufficient", "Data Insufficient"),
    ("awaiting_candidate_input", "Awaiting Candidate Input"),
    ("awaiting_employer_response", "Awaiting Employer Response"),
    ("awaiting_university_response", "Awaiting University Response"),
    ("awaiting_court_response", "Awaiting Court Response"),

    # Successful / terminal states
    ("clear", "BGV Clear"),
    ("completed", "BGV Completed"),
    ("closed", "BGV Closed"),
    ("verified", "Verified"),
    ("unable_to_verify", "Unable To Verify"),
    ("discrepancy", "Discrepancy Found"),

    # Failure states
    ("failed", "BGV Failed"),
    ("cancelled", "BGV Cancelled"),
    ("rejected", "BGV Rejected"),
    ("expired", "BGV Expired"),
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
    candidate_phone = models.CharField(max_length=20, blank=True,null=True)
    cover_letter = models.TextField(blank=True)

    location = models.CharField(max_length=255,blank=True,null=True)
    availibility = models.CharField(blank=True,null=True)
    current_employer = models.CharField(max_length=100,blank=True,null=True)
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
    
    bgv_status = models.CharField(
        max_length=50,
        choices=BGV_STATUS_CHOICES,
        default='pending_schedule'
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
    linkedin_url = models.CharField(blank=True, max_length=500,null=True)
    
    # Portfolio/GitHub
    portfolio_url = models.CharField(blank=True, max_length=500,null=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
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
    offer_accepted_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True) #Status of Application (for archiving)

    is_duplicate = models.BooleanField(default=False)
    is_shortlisted = models.BooleanField(default=False)
    is_selected = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)

    slot_link = models.URLField(null=True,blank=True)
    inperson_link = models.URLField(null=True,blank=True)
    candidate_history = models.JSONField(null=True,blank=True,default=list)

    consolidated_feedback_avg = models.FloatField(default=0)
    rejection_reason = models.TextField(null=True,blank=True)
    offer_decline_reason = models.TextField(null=True,blank=True)
    
    referral_name = models.CharField(null=True,blank=True)
    referral_email = models.CharField(null=True,blank=True)
    referral_phone = models.CharField(null=True,blank=True)
    referral_emp_code = models.CharField(null=True,blank=True)
    referral_designation = models.CharField(null=True,blank=True)
    referral_department = models.CharField(null=True,blank=True)

    # Interview No-show / Reschedule tracking (used by dashboard)
    no_show_count = models.PositiveIntegerField(default=0)
    reschedule_count = models.PositiveIntegerField(default=0)

    #Interview Details
    interview_scheduled_at = models.DateTimeField(null=True,blank=True)
    interview_end_at = models.DateTimeField(null=True,blank=True)
    interviewer_name = models.CharField(null=True,blank=True)
    interview_link = models.TextField(null=True,blank=True)
    feedback_link = models.TextField(null=True,blank=True)
    round_name = models.CharField(null=True,blank=True,choices=INTERVIEW_CHOICES)
    
    class Meta:
        db_table = 'job_applications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['source']),
            models.Index(fields=['application_link']),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._skip_engine_trigger = False
    
    def __str__(self):
        return f"{self.candidate_name} - {self.job.job_title}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        old_joining_date = None
        if not is_new:
            try:
                old_obj = JobApplication.objects.get(pk=self.pk)
                old_status = old_obj.status
                old_joining_date = old_obj.joining_date
            except JobApplication.DoesNotExist:
                pass

        trigger_engine_joined = False

        # Manual transition detection (if status was manually changed to joined)
        # Skip if _skip_engine_trigger is set (automation_engine already handling this)
        if not is_new and self.status == 'joined' and old_status != 'joined':
            if not getattr(self, '_skip_engine_trigger', False):
                trigger_engine_joined = True

        super().save(*args, **kwargs)

        if trigger_engine_joined:
            from onboarding.utils.engine import automation_engine
            # Trigger engine for manual status jump to joined
            automation_engine(self, old_status, 'joined')
        
        # If joining_date was previously in the past (which may have auto-transitioned
        # the candidate to 'joined') and is now moved to a future date, revert the
        # candidate back to 'joining_pending' and adjust Job/MRF counts/status.
        try:
            from datetime import date
            from django.utils import timezone as _tz

            if (not is_new) and old_status == 'joined' and old_joining_date != self.joining_date and (self.joining_date is None or self.joining_date > date.today()):
                # Only act if candidate is currently marked as joined
                if self.status == 'joined':
                    job = self.job
                    if job:
                        # Recompute positions_filled based on other joined candidates
                        other_joined = job.applications.filter(status='joined').exclude(pk=self.pk).count()
                        job.positions_filled = other_joined
                        # If positions filled are now less than required, set job->joining_pending
                        if job.positions_filled < job.no_of_positions:
                            job.status = 'joining_pending'
                        # Persist job changes
                        job.save(update_fields=['positions_filled', 'status'])

                        # Sync MRF status if needed
                        if hasattr(job, 'mrf') and job.mrf:
                            try:
                                if job.mrf.status == 'filled' and job.positions_filled < job.no_of_positions:
                                    job.mrf.status = 'joining_pending'
                                    job.mrf.save(update_fields=['status'])
                            except Exception:
                                pass

                    # Revert candidate status in DB directly to avoid recursive engine triggers
                    JobApplication.objects.filter(pk=self.pk).update(status='joining_pending', updated_at=_tz.now())
                    from onboarding.models import ApprovalNote
                    ApprovalNote.objects.filter(candidate=self).update(status='joining_pending', updated_at=_tz.now())
                    # Keep in-memory instance in sync
                    self.status = 'joining_pending'
        except Exception as e:
            # Non-fatal — don't block save on revert failures
            import logging
            logging.getLogger(__name__).error(f"Failed to revert joining status for {self.pk}: {e}", exc_info=True)
            
    def get_platform_name(self):
        """Get the platform name from application link"""
        if self.application_link:
            return self.application_link.get_platform_display()
        return self.get_source_display()
    
    def soft_delete(self):
        """Soft delete this application (for archive consistency)."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])


class JobAssignmentHistory(models.Model):
    """Track job assignment and status history"""
    
    ACTION_CHOICES = [
        ('created', 'Job Created'),
        ('assigned', 'Assigned to Consultancy'),
        ('reassigned', 'Reassigned to Another Consultancy'),
        ('unassigned', 'Unassigned from Consultancy'),
        ('assigned_internal', 'Assigned to Internal HR'),
        ('reassigned_internal', 'Reassigned to Another Internal HR'),
        ('status_changed', 'Status Changed'),
        ('priority_changed', 'Priority Changed'),
        ('closed', 'Job Closed'),
        ('filled', 'Position Filled'),
        ('reopened', 'Job Reopened'),
        ('cancelled', 'Job Cancelled'),
        ('hold', 'Job Put on Hold'),
        ('hold_released', 'Job Hold Released'),
        ('deleted', 'Job Soft Deleted'),
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
    
    created_at = models.DateTimeField(default=timezone.now)
    
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
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    #Referrer Info    
    referral_name = models.CharField(null=True,blank=True)
    referral_email = models.CharField(null=True,blank=True)
    referral_phone = models.CharField(null=True,blank=True)
    referral_emp_code = models.CharField(null=True,blank=True)
    referral_designation = models.CharField(null=True,blank=True)
    referral_department = models.CharField(null=True,blank=True)
    position_title = models.CharField(null=True,blank=True)
    
    is_touched = models.BooleanField(default=False, help_text="Has the candidate been touched at least once?")
    touched_at = models.DateTimeField(null=True, blank=True, help_text="When was the candidate last touched?")
    is_active = models.BooleanField(default=True, help_text="Is the referral application active?")
    
    class Meta:
        db_table = 'referral_applications'
        ordering = ['-created_at']

    def soft_delete(self):
        """Soft delete this referral application (sets is_active=False).
        Consistent with all list/analytics filters using is_active=True.
        """
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

class ApplicationSource(models.TextChoices):
    CAREER = 'career_page', 'Career Page'
    LINKEDIN = 'linkedin', 'LinkedIn'
    NAUKRI = 'naukri', 'Naukri'
    INDEED = 'indeed', 'Indeed'


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job,on_delete=models.CASCADE,null=True,blank=True,related_name='platform_applications')

    department = models.ForeignKey('mrf.Department', on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey('mrf.Designation', on_delete=models.SET_NULL, null=True, blank=True)

    source = models.CharField(max_length=20, choices=ApplicationSource.choices)

    resume = models.FileField(upload_to='applications/')
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(default=0)

    notes = models.TextField(blank=True)
    position_title = models.CharField(null=True, blank=True)

    candidate_name = models.CharField(max_length=255, blank=True)
    candidate_email = models.EmailField(blank=True, null=True)
    candidate_phone = models.CharField(max_length=20, blank=True,null=True)

    location = models.CharField(max_length=255,blank=True,null=True)
    current_employer = models.CharField(max_length=100,blank=True,null=True)

    skill = models.JSONField(blank=True,null=True,default=list)
    education = models.JSONField(blank=True,null=True,default=list)

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

    cover_letter = models.TextField(blank=True,null=True)
    availibility = models.CharField(blank=True,null=True)
    notice_period = models.CharField(max_length=50, blank=True,null=True)

    current_ctc = models.CharField(max_length=50, blank=True,null=True)
    expected_ctc = models.CharField(max_length=50, blank=True,null=True)

    linkedin_url = models.URLField(blank=True, max_length=500,null=True)
    portfolio_url = models.URLField(blank=True, max_length=500,null=True)
    
    match_score = models.DecimalField(blank=True,null=True,max_digits=5,decimal_places=2,help_text="Score out of 0 to 100")
    resume_report = models.FileField(blank=True,null=True,upload_to='reports/', help_text='Candidate resume report.')
    is_duplicate = models.BooleanField(default=False)
    candidate_history = models.JSONField(null=True,blank=True,default=list)

    is_rejected = models.BooleanField(default=False)
    rejected_by = models.ForeignKey("accounts.user",on_delete=models.SET_NULL,null=True,blank=True)
    rejection_reason = models.TextField(null=True,blank=True)

    is_touched = models.BooleanField(default=False, help_text="Has the candidate been touched at least once?")
    touched_at = models.DateTimeField(null=True, blank=True, help_text="When was the candidate last touched?")
    is_active = models.BooleanField(default=True, help_text="Is the platform application active?")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def soft_delete(self):
        """Soft delete this platform application (sets is_active=False)."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    class Meta:
        db_table = 'applications'
        ordering = ['-created_at']