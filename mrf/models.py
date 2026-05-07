from django.db import models,transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import User,Company
import uuid
from datetime import datetime, time, timedelta
from django.db.models import Q, UniqueConstraint,Max
from slots.models import Interviewer
import logging

logger = logging.getLogger(__name__)

class Department(models.Model):
    """Department master - easily add/modify/delete"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE,null=True,blank=True)
    code = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'],
                name='uniq_department_name_per_company'
            ),
            models.UniqueConstraint(
                fields=['company', 'code'],
                name='uniq_department_code_per_company'
            ),
        ]
    
    def save(self, *args, **kwargs):
        if not self.code:
            with transaction.atomic():
                last_code = (
                    Department.objects
                    .filter(company=self.company,code__startswith='DEP')
                    .aggregate(max_code=Max('code'))
                    ['max_code']
                )

                if last_code:
                    last_number = int(last_code.replace('DEP', ''))
                    new_number = last_number + 1
                else:
                    new_number = 1

                self.code = f"DEP{new_number:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Designation(models.Model):
    """Designation master - easily add/modify/delete"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE,null=True,blank=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    tat_days = models.IntegerField(null=True,blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='designations', blank=True, null=True)
    key_responsibility = models.TextField(null=True,blank=True)
    required_qualifications = models.TextField(null=True,blank=True)
    skills_competencies = models.TextField(null=True,blank=True)
    salary_range = models.CharField(max_length=100, help_text="e.g., '5-8 LPA'",blank=True,null=True)
    expirience = models.CharField(max_length=100, help_text="e.g., '1-3 years'",blank=True,null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'code'],
                name='uniq_designation_code_per_company'
            ),
        ]
    
    def save(self, *args, **kwargs):
        if not self.department:
            raise ValidationError("Department is required to generate designation code")
        if not self.code:
            with transaction.atomic():
                dept_code = self.department.code

                last_code = (
                    Designation.objects
                    .select_for_update()
                    .filter(company=self.company,department=self.department)
                    .aggregate(max_code=Max('code'))
                    ['max_code']
                )

                next_number = (
                    int(last_code.split('DSG')[-1]) + 1 if last_code else 1
                )

                self.code = f"{dept_code}-DSG{next_number:03d}"

        if not self.expirience and self.skills_competencies:
            try:
                from .utils import parse_expirience
                extracted = parse_expirience(self.skills_competencies)
                if extracted:
                    self.expirience = extracted[:100]  # safety for max_length
            except Exception as e:
                print("GPT parsing failed:", e)  
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.name


class WorkflowTemplate(models.Model):
    """Workflow template - a collection of approval levels"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="e.g., 'HR First Workflow', 'Admin First Workflow'")
    description = models.TextField(blank=True, help_text="Description of this workflow")
    company = models.ForeignKey(Company, on_delete=models.CASCADE,null=True,blank=True)
    is_active = models.BooleanField(default=True, help_text="Set to False to disable this workflow")
    is_default = models.BooleanField(default=False, help_text="Use this as default for new MRFs")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        default_text = " (Default)" if self.is_default else ""
        return f"{self.name}{default_text}"
    
    def save(self, *args, **kwargs):
        # If this is set as default, remove default from others
        if self.is_default and self.company:
            WorkflowTemplate.objects.filter(company=self.company, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    def get_levels(self):
        """Get all approval levels for this workflow"""
        return self.levels.filter(is_active=True).order_by('order', 'level')


class ApprovalWorkflow(models.Model):
    """Individual approval level in a workflow template"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE,null=True,blank=True)
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name='levels')
    level = models.IntegerField(help_text="Approval level (1, 2, 3, etc.)")
    required_role = models.CharField(max_length=20, help_text="Role required for this level")
    is_active = models.BooleanField(default=True)
    approver = models.ForeignKey(User,on_delete=models.PROTECT,related_name='levels_approver',help_text="User responsible for approvals at this level",blank=True,null=True)
    order = models.IntegerField(help_text="Order of execution")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['template', 'order', 'level']
        unique_together = ['template', 'level']
    
    def __str__(self):
        return f"{self.template.name} - Level {self.level} ({self.required_role})"


class MRF(models.Model):
    """Main MRF (Manpower Requisition Form) model"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_level_1', 'Pending Level 1 Approval'),
        ('pending_level_2', 'Pending Level 2 Approval'),
        ('pending_level_3', 'Pending Level 3 Approval'),
        ('on_hold', 'On Hold'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revision_required', 'Revision Required'),
        ('joining_pending', 'Joining Pending'),
        ('filled', 'Position Filled'),
    ]
    
    CASE_STUDY_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
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

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE,null=True,blank=True)

    # Workflow Assignment - IMPORTANT: Links MRF to specific workflow
    workflow_template = models.ForeignKey(
        WorkflowTemplate, 
        on_delete=models.PROTECT, 
        related_name='mrfs',
        help_text="The workflow template this MRF follows",
        null=True,
        blank=True
    )

    # Private MRF fields
    is_private = models.BooleanField(
        default=False,
        help_text="If True, this MRF uses direct approval levels and has restricted visibility"
    )
    selected_viewers = models.ManyToManyField(
        User,
        blank=True,
        related_name='viewable_private_mrfs',
        help_text="Users who can view this private MRF (in addition to creator, approvers, and admin)"
    )
    
    # Basic Details
    mrf_name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='mrfs')
    date_of_request = models.DateField(default=timezone.now)
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='mrfs_created')
    requested_by_name = models.CharField(max_length=255)
    requested_by_designation = models.CharField(max_length=255)
    
    # Position Details
    designation = models.ForeignKey(Designation, on_delete=models.PROTECT, related_name='mrfs')
    team = models.CharField(max_length=255)
    position_department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='position_mrfs')
    no_of_vacancies = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=255, default='ahmedabad')
    job_type = models.CharField(max_length=50,choices=JOB_TYPE_CHOICES,default="work_from_office")
    
    # Optional Fields
    resigned_crafter_name = models.CharField(max_length=255, blank=True, null=True)
    resigned_crafter_ecode = models.CharField(max_length=100, blank=True, null=True)
    resigned_crafter_designation = models.CharField(max_length=100, blank=True, null=True)
    
    # Job Details
    key_responsibility = models.TextField(null=True,blank=True)
    required_qualifications = models.TextField(null=True,blank=True)
    experience_range = models.CharField(max_length=100, help_text="e.g., '2-5 years'")
    skills_competencies = models.TextField(null=True,blank=True)
    
    # Justification
    business_justification = models.TextField()
    
    # Compensation
    salary_range = models.CharField(max_length=100, help_text="e.g., '5-8 LPA'")
    
    # Recruitment Details
    expected_date_of_joining = models.DateField()
    
    # Interview Details
    case_study_required = models.CharField(max_length=10, choices=CASE_STUDY_CHOICES, default='no')
    technical_interview_1 = models.CharField(max_length=255, help_text="Name of interviewer", blank=True, null=True)
    technical_interview_2 = models.CharField(max_length=255, blank=True, null=True, help_text="Optional")
    final_interview = models.CharField(max_length=255, help_text="Name of final interviewer", blank=True, null=True)

    interviewer_email_1 = models.EmailField(max_length=50, blank=True, null=True, help_text="Email of HR round interviewer")
    interviewer_email_2 = models.EmailField(max_length=50, blank=True, null=True, help_text="Email of Technical round interviewer")
    interviewer_email_3 = models.EmailField(max_length=50, blank=True, null=True, help_text="Email of Case study round interviewer")
    interviewer_email_final = models.EmailField(max_length=50, blank=True, null=True, help_text="Email of final round interviewer")
    interviewer_email_management_client = models.EmailField(max_length=50, blank=True, null=True, help_text="Interviewer email of management client interview")

    technical_interviewers = models.ManyToManyField(
        Interviewer,
        blank=True,
        related_name="technical_mrfs"
    )

    hr_interviewer = models.ForeignKey(
        Interviewer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_mrfs"
    )

    case_study_interviewer = models.ForeignKey(
        Interviewer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case_study_mrfs"
    )

    final_interviewer = models.ForeignKey(
        Interviewer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="final_mrfs"
    )

    management_client_interviewer = models.ForeignKey(
        Interviewer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="management_client_mrfs"
    )
    # HR Use Only
    requisition_no = models.CharField(max_length=255, blank=True, null=True)
    date_received = models.DateField(blank=True, null=True)
    
    # Workflow State
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    current_approval_level = models.IntegerField(default=0)

    #Hold
    previous_status = models.CharField(
        max_length=50, 
        choices=[(choice[0], choice[1]) for choice in STATUS_CHOICES if choice[0] != 'on_hold'],  # Exclude 'on_hold'
        blank=True, 
        null=True, 
        help_text="Status before being put on hold (for restoration)"
    )
    held_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when put on hold")
    hold_reason = models.TextField(blank=True, help_text="Reason for holding the job")
    held_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mrf_holder',null=True,blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'MRF'
        verbose_name_plural = 'MRFs'
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'requisition_no'],
                name='uniq_mrf_requisition_no_per_company'
            ),
        ]
    
    def __str__(self):
        wf_name = self.workflow_template.name if self.workflow_template else 'Private'
        return f"MRF-{self.requisition_no or self.id} - {self.department.name} ({wf_name})"
    
    def save(self, *args, **kwargs):
        self.interviewer_email_1 = self.hr_interviewer.email if self.hr_interviewer else None
        self.interviewer_email_3 = self.case_study_interviewer.email if self.case_study_interviewer else None
        self.interviewer_email_final = self.final_interviewer.email if self.final_interviewer else None
        self.interviewer_email_management_client = (
            self.management_client_interviewer.email if self.management_client_interviewer else None
        )

        # For technical interviewers, pick the first one if exists
        first_technical = self.technical_interviewers.first()
        self.interviewer_email_2 = first_technical.email if first_technical else None

        # Auto-generate requisition number after final approval
        if not self.company:
            raise ValidationError("Company is required to generate department code")
        
        # Private MRFs don't require a workflow_template
        if not self.is_private and not self.workflow_template_id:
            raise ValidationError("Non-private MRFs require a workflow template")

        if self.status == 'approved' and not self.requisition_no:
            self.requisition_no = self.generate_requisition_no()
            self.date_received = self.calculate_date_received()
            self.approved_at = timezone.now()

        if self.status == 'revision_required':
            self.rejected_at = timezone.now()
        
        super().save(*args, **kwargs)

        # Log activity for private MRFs (audit trail)
        if self.is_private:
            logger.info(
                f"[PRIVATE MRF] id={self.id} status={self.status} "
                f"by={self.requested_by_id} company={self.company_id}"
            )
    
    def generate_requisition_no(self):
        """Generate unique requisition number"""
        date = timezone.now().date()
        designation = self.designation
        department = self.department
        with transaction.atomic():
            count = MRF.objects.filter(company=self.company,
                requisition_no__startswith=f'MRF_{designation}_{department}'
            ).count() + 1
        return f'MRF_{designation}_{department}_{count:05d}_{date}'
    
    def calculate_date_received(self):
        """Calculate date received based on approval time"""
        now = timezone.now()
        
        # If approved after 5 PM, set to next working day
        if now.time() >= time(17, 0):  # 5 PM
            next_day = now.date() + timedelta(days=1)
            # Skip weekends
            while next_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
                next_day += timedelta(days=1)
            return next_day
        
        return now.date()
    
    def get_next_approvers(self):
        """Get list of users who can approve at current level"""
        next_level = self.current_approval_level + 1

        if self.is_private:
            # Private MRF: use direct approval levels
            private_level = self.private_approval_levels.filter(
                level=next_level,
                is_active=True
            ).first()
            if not private_level:
                return []
            return User.objects.filter(
                id=private_level.approver.id,
                is_active=True
            )

        # Standard MRF: use workflow template
        workflow = self.workflow_template.levels.filter(
            level=next_level,
            is_active=True
        ).first()
        
        if not workflow:
            return []
        
        return User.objects.filter(
            role=workflow.required_role,
            is_active=True,
            id = workflow.approver.id,
            company=self.requested_by.company
        )
    
    def can_user_approve(self, user):
        """Check if user can approve at current level"""
        if self.status not in ['pending_level_1', 'pending_level_2', 'pending_level_3']:
            return False
        
        next_level = self.current_approval_level + 1

        if self.is_private:
            # Private MRF: check direct approval levels
            private_level = self.private_approval_levels.filter(
                level=next_level,
                is_active=True
            ).first()
            if not private_level:
                return False
            return user.id == private_level.approver.id

        # Standard MRF: use workflow template
        workflow = self.workflow_template.levels.filter(
            level=next_level,
            is_active=True
        ).first()
        
        if not workflow:
            return False
        
        return user.role == workflow.required_role and user.id == workflow.approver.id
    
    def get_workflow_summary(self):
        """Get workflow summary for display"""
        if self.is_private:
            levels = self.private_approval_levels.filter(is_active=True).order_by('level')
            return [
                {
                    'level': level.level,
                    'role': level.approver.role,
                    'approver': level.approver.id,
                    'approver_name': level.approver.name,
                    'order': level.level
                }
                for level in levels
            ]

        levels = self.workflow_template.get_levels()
        return [
            {
                'level': level.level,
                'role': level.required_role,
                'approver': level.approver.id,
                'order': level.order
            }
            for level in levels
        ]

    def can_user_view_private(self, user):
        """Check if user can view this private MRF"""
        if not self.is_private:
            return True
        
        # Admin can always see
        if user.role == 'admin':
            return True
        
        # Creator can see
        if self.requested_by_id == user.id:
            return True
        
        # Selected viewers can see
        if self.selected_viewers.filter(id=user.id).exists():
            return True
        
        # Approvers at any level can see
        if self.private_approval_levels.filter(approver=user).exists():
            return True
        
        # Assigned HR (via job) can see
        job = getattr(self, 'job', None)
        if job:
            if (job.assigned_to_internal_hr_id == user.id or
                job.assigned_to_consultancy_id == user.id or
                job.assigned_internal_hrs.filter(id=user.id).exists() or
                job.assigned_consultancies.filter(id=user.id).exists()):
                return True
        
        return False


class MRFApproval(models.Model):
    """Track approval history for each MRF"""
    
    ACTION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revision_requested', 'Revision Requested'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE,null=True,blank=True)
    mrf = models.ForeignKey(MRF, on_delete=models.CASCADE, related_name='approvals')
    level = models.IntegerField()
    approver = models.ForeignKey(User, on_delete=models.PROTECT, related_name='mrf_approvals')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.mrf.requisition_no or self.mrf.id} - Level {self.level} - {self.action}"


class MRFRevision(models.Model):
    """Track MRF revisions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE,null=True,blank=True)
    mrf = models.ForeignKey(MRF, on_delete=models.CASCADE, related_name='revisions')
    revised_by = models.ForeignKey(User, on_delete=models.PROTECT)
    revision_notes = models.TextField()
    previous_data = models.JSONField(help_text="Store previous MRF data")
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Revision for {self.mrf.requisition_no or self.mrf.id}"


class PrivateMRFApprovalLevel(models.Model):
    """Direct approval levels for private MRFs (no workflow template needed)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mrf = models.ForeignKey(
        MRF,
        on_delete=models.CASCADE,
        related_name='private_approval_levels',
        help_text="The private MRF this approval level belongs to"
    )
    level = models.IntegerField(help_text="Approval level (1, 2, 3, etc.)")
    approver = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='private_mrf_approval_levels',
        help_text="User who can approve at this level"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['mrf', 'level']
        unique_together = ['mrf', 'level']

    def __str__(self):
        return f"Private MRF {self.mrf_id} - Level {self.level} ({self.approver.name})"
    