from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import User
import uuid
from datetime import datetime, time, timedelta


class Department(models.Model):
    """Department master - easily add/modify/delete"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Designation(models.Model):
    """Designation master - easily add/modify/delete"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class WorkflowTemplate(models.Model):
    """Workflow template - a collection of approval levels"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="e.g., 'HR First Workflow', 'Admin First Workflow'")
    description = models.TextField(blank=True, help_text="Description of this workflow")
    is_active = models.BooleanField(default=True, help_text="Set to False to disable this workflow")
    is_default = models.BooleanField(default=False, help_text="Use this as default for new MRFs")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        default_text = " (Default)" if self.is_default else ""
        return f"{self.name}{default_text}"
    
    def save(self, *args, **kwargs):
        # If this is set as default, remove default from others
        if self.is_default:
            WorkflowTemplate.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    def get_levels(self):
        """Get all approval levels for this workflow"""
        return self.levels.filter(is_active=True).order_by('order', 'level')


class ApprovalWorkflow(models.Model):
    """Individual approval level in a workflow template"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name='levels')
    level = models.IntegerField(help_text="Approval level (1, 2, 3, etc.)")
    required_role = models.CharField(max_length=20, help_text="Role required for this level")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(help_text="Order of execution")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revision_required', 'Revision Required'),
    ]
    
    CASE_STUDY_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    
    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Workflow Assignment - IMPORTANT: Links MRF to specific workflow
    workflow_template = models.ForeignKey(
        WorkflowTemplate, 
        on_delete=models.PROTECT, 
        related_name='mrfs',
        help_text="The workflow template this MRF follows"
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
    location = models.CharField(max_length=50, default='ahmedabad')
    
    # Optional Fields
    resigned_crafter_name = models.CharField(max_length=255, blank=True, null=True)
    resigned_crafter_ecode = models.CharField(max_length=100, blank=True, null=True)
    
    # Job Details
    key_responsibility = models.TextField()
    required_qualifications = models.TextField()
    experience_range = models.CharField(max_length=100, help_text="e.g., '2-5 years'")
    skills_competencies = models.TextField()
    
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

    interviewer_email_1 = models.EmailField(max_length=50, help_text="Email of interviewer")
    interviewer_email_2 = models.EmailField(max_length=50, blank=True, null=True, help_text="Optional")
    interviewer_email_final = models.EmailField(max_length=50, help_text="Email of final interviewer")
    
    # HR Use Only
    requisition_no = models.CharField(max_length=50, unique=True, blank=True, null=True)
    date_received = models.DateField(blank=True, null=True)
    
    # Workflow State
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    current_approval_level = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'MRF'
        verbose_name_plural = 'MRFs'
    
    def __str__(self):
        return f"MRF-{self.requisition_no or self.id} - {self.department.name} ({self.workflow_template.name})"
    
    def save(self, *args, **kwargs):
        # Auto-generate requisition number after final approval
        if self.status == 'approved' and not self.requisition_no:
            self.requisition_no = self.generate_requisition_no()
            self.date_received = self.calculate_date_received()
            self.approved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def generate_requisition_no(self):
        """Generate unique requisition number"""
        date = timezone.now().date()
        designation = self.designation
        department = self.department
        count = MRF.objects.filter(
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
        workflow = self.workflow_template.levels.filter(
            level=next_level,
            is_active=True
        ).first()
        
        if not workflow:
            return []
        
        return User.objects.filter(
            role=workflow.required_role,
            is_active=True,
            company=self.requested_by.company
        )
    
    def can_user_approve(self, user):
        """Check if user can approve at current level"""
        if self.status not in ['pending_level_1', 'pending_level_2', 'pending_level_3']:
            return False
        
        next_level = self.current_approval_level + 1
        workflow = self.workflow_template.levels.filter(
            level=next_level,
            is_active=True
        ).first()
        
        if not workflow:
            return False
        
        return user.role == workflow.required_role
    
    def get_workflow_summary(self):
        """Get workflow summary for display"""
        levels = self.workflow_template.get_levels()
        return [
            {
                'level': level.level,
                'role': level.required_role,
                'order': level.order
            }
            for level in levels
        ]


class MRFApproval(models.Model):
    """Track approval history for each MRF"""
    
    ACTION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revision_requested', 'Revision Requested'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mrf = models.ForeignKey(MRF, on_delete=models.CASCADE, related_name='approvals')
    level = models.IntegerField()
    approver = models.ForeignKey(User, on_delete=models.PROTECT, related_name='mrf_approvals')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.mrf.requisition_no or self.mrf.id} - Level {self.level} - {self.action}"


class MRFRevision(models.Model):
    """Track MRF revisions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mrf = models.ForeignKey(MRF, on_delete=models.CASCADE, related_name='revisions')
    revised_by = models.ForeignKey(User, on_delete=models.PROTECT)
    revision_notes = models.TextField()
    previous_data = models.JSONField(help_text="Store previous MRF data")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Revision for {self.mrf.requisition_no or self.mrf.id}"