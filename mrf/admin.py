from django.contrib import admin
from .models import (
    Department, Designation, MRF, MRFApproval, MRFRevision, 
    ApprovalWorkflow, WorkflowTemplate, PrivateMRFApprovalLevel
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'company', 'is_active', 'created_at']
    list_filter = ['is_active', 'company']
    search_fields = ['name', 'code']
    readonly_fields = ['code', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'name', 'code', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'department', 'company', 'tat_days', 
        'salary_range', 'expirience', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'department', 'company']
    search_fields = ['name', 'code', 'department__name', 'skills_competencies']
    readonly_fields = ['code', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Details', {
            'fields': ('company', 'department', 'name', 'code', 'tat_days', 'is_active')
        }),
        ('Job Description & Requirements', {
            'fields': ('key_responsibility', 'required_qualifications', 'skills_competencies', 'salary_range', 'expirience')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ApprovalWorkflowInline(admin.TabularInline):
    model = ApprovalWorkflow
    extra = 1
    fields = ['level', 'required_role', 'approver', 'order', 'is_active']
    ordering = ['order', 'level']


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'company', 'is_active', 'is_default', 'get_total_levels', 'created_at']
    list_filter = ['is_active', 'is_default', 'department', 'company']
    search_fields = ['name', 'description', 'department__name']
    inlines = [ApprovalWorkflowInline]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Template Details', {
            'fields': ('company', 'department', 'name', 'description', 'is_active', 'is_default')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_levels(self, obj):
        return obj.levels.filter(is_active=True).count()
    get_total_levels.short_description = 'Total Levels'


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ['template', 'level', 'required_role', 'approver', 'order', 'is_active', 'created_at']
    list_filter = ['template', 'is_active', 'required_role']
    search_fields = ['template__name', 'approver__name', 'approver__email', 'required_role']
    ordering = ['template', 'order', 'level']
    readonly_fields = ['created_at', 'updated_at']

class PrivateMRFApprovalLevelInline(admin.TabularInline):
    model = PrivateMRFApprovalLevel
    extra = 0
    fields = ['level', 'approver', 'is_active', 'created_at']
    readonly_fields = ['created_at']
    ordering = ['level']


class MRFApprovalInline(admin.TabularInline):
    model = MRFApproval
    extra = 0
    fields = ['level', 'approver', 'action', 'comments', 'rejection_reason', 'created_at']
    readonly_fields = ['level', 'approver', 'action', 'comments', 'rejection_reason', 'created_at']
    can_delete = False
    ordering = ['level', 'created_at']

class MRFRevisionInline(admin.StackedInline):
    model = MRFRevision
    extra = 0
    fields = ['revised_by', 'revision_notes', 'previous_data', 'created_at']
    readonly_fields = ['revised_by', 'revision_notes', 'previous_data', 'created_at']
    can_delete = False
    ordering = ['-created_at']


@admin.register(MRF)
class MRFAdmin(admin.ModelAdmin):
    list_display = [
        'requisition_no', 'mrf_name', 'workflow_template', 'department', 'designation', 
        'requested_by', 'status', 'priority', 'job_type', 'no_of_vacancies',
        'is_private', 'is_active', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'is_private', 'is_active', 'job_type',
        'workflow_template', 'department', 'designation', 'location', 'created_at'
    ]
    search_fields = [
        'requisition_no', 'mrf_name', 'requested_by__name', 'requested_by__email',
        'requested_by_name', 'department__name', 'designation__name'
    ]
    readonly_fields = []
    filter_horizontal = ('selected_viewers', 'technical_interviewers')
    inlines = [PrivateMRFApprovalLevelInline, MRFApprovalInline, MRFRevisionInline]
    
    fieldsets = (
        ('Workflow & Status', {
            'fields': (
                'workflow_template', 'status', 'previous_status',
                'priority', 'current_approval_level', 'is_active'
            )
        }),
        ('Private MRF Settings', {
            'fields': (
                'is_private', 'selected_viewers'
            ),
            'classes': ('collapse',)
        }),
        ('Basic Details', {
            'fields': (
                'company', 'department', 'mrf_name', 'date_of_request',
                'requested_by', 'requested_by_name', 'requested_by_designation'
            )
        }),
        ('Position Details', {
            'fields': (
                'designation', 'team', 'position_department', 
                'no_of_vacancies', 'location', 'job_type'
            )
        }),
        ('Replacement Details', {
            'fields': (
                'resigned_crafter_name', 'resigned_crafter_ecode', 'resigned_crafter_designation'
            ),
            'classes': ('collapse',)
        }),
        ('Job Details', {
            'fields': (
                'key_responsibility', 'required_qualifications', 
                'experience_range', 'skills_competencies'
            )
        }),
        ('Justification & Compensation', {
            'fields': (
                'business_justification', 'salary_range', 'expected_date_of_joining'
            )
        }),
        ('Interview Details', {
            'fields': (
                'case_study_required',
                'technical_interview_1', 'technical_interview_2', 'final_interview',
                'technical_interviewers', 'hr_interviewer', 'case_study_interviewer',
                'final_interviewer', 'management_client_interviewer',
                'interviewer_email_1', 'interviewer_email_2', 'interviewer_email_3',
                'interviewer_email_final', 'interviewer_email_management_client'
            )
        }),
        ('Hold Details', {
            'fields': (
                'held_by', 'held_at', 'hold_reason'
            ),
            'classes': ('collapse',)
        }),
        ('HR Use Only', {
            'fields': (
                'requisition_no', 'date_received'
            )
        }),
        ('Timestamps', {
            'fields': (
                'submitted_at', 'approved_at', 'rejected_at', 'created_at', 'updated_at'
            )
        }),
    )


@admin.register(MRFApproval)
class MRFApprovalAdmin(admin.ModelAdmin):
    list_display = ['mrf', 'level', 'approver', 'action', 'comments', 'created_at']
    list_filter = ['action', 'level', 'created_at']
    search_fields = ['mrf__requisition_no', 'approver__name', 'approver__email']
    readonly_fields = ['created_at']


@admin.register(MRFRevision)
class MRFRevisionAdmin(admin.ModelAdmin):
    list_display = ['mrf', 'revised_by', 'revision_notes', 'created_at']
    search_fields = ['mrf__requisition_no', 'revised_by__name', 'revised_by__email']
    readonly_fields = ['created_at']


class PrivateMRFApprovalLevelInline(admin.TabularInline):
    model = PrivateMRFApprovalLevel
    extra = 1
    fields = ['level', 'approver', 'is_active']
    ordering = ['level']


@admin.register(PrivateMRFApprovalLevel)
class PrivateMRFApprovalLevelAdmin(admin.ModelAdmin):
    list_display = ['mrf', 'level', 'approver', 'is_active', 'created_at']
    list_filter = ['is_active', 'level', 'created_at']
    search_fields = ['mrf__requisition_no', 'approver__name', 'approver__email']
    readonly_fields = ['created_at']
