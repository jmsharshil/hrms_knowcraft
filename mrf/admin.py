from django.contrib import admin
from .models import (
    Department, Designation, MRF, MRFApproval, MRFRevision, 
    ApprovalWorkflow, WorkflowTemplate
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ['name', 'tat_days', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


class ApprovalWorkflowInline(admin.TabularInline):
    model = ApprovalWorkflow
    extra = 1
    fields = ['level', 'required_role', 'order', 'is_active']
    ordering = ['order', 'level']


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'is_default', 'get_total_levels', 'created_at']
    list_filter = ['is_active', 'is_default']
    search_fields = ['name', 'description']
    inlines = [ApprovalWorkflowInline]
    
    def get_total_levels(self, obj):
        return obj.levels.filter(is_active=True).count()
    get_total_levels.short_description = 'Total Levels'


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ['template', 'level', 'required_role', 'order', 'is_active', 'created_at']
    list_filter = ['template', 'is_active', 'required_role']
    ordering = ['template', 'order', 'level']


@admin.register(MRF)
class MRFAdmin(admin.ModelAdmin):
    list_display = [
        'requisition_no', 'workflow_template', 'department', 'designation', 
        'requested_by', 'status', 'no_of_vacancies', 'created_at'
    ]
    list_filter = ['status', 'workflow_template', 'department', 'designation', 'location']
    search_fields = ['requisition_no', 'requested_by__name', 'requested_by__email']
    readonly_fields = [
        'requisition_no', 'date_received', 'created_at', 'updated_at', 
        'submitted_at', 'approved_at', 'workflow_template'
    ]
    
    fieldsets = (
        ('Workflow', {
            'fields': ('workflow_template', 'status', 'current_approval_level')
        }),
        ('Basic Details', {
            'fields': ('department', 'date_of_request', 'requested_by', 
                      'requested_by_name', 'requested_by_designation')
        }),
        ('Position Details', {
            'fields': ('designation', 'team', 'position_department', 
                      'no_of_vacancies', 'location')
        }),
        ('Optional Fields', {
            'fields': ('resigned_crafter_name', 'resigned_crafter_ecode', 'resigned_crafter_designation'),
            'classes': ('collapse',)
        }),
        ('Job Details', {
            'fields': ('key_responsibility', 'required_qualifications', 
                      'experience_range', 'skills_competencies')
        }),
        ('Justification & Compensation', {
            'fields': ('business_justification', 'salary_range', 'expected_date_of_joining')
        }),
        ('Interview Details', {
            'fields': ('case_study_required', 'technical_interview_1', 
                      'technical_interview_2', 'final_interview')
        }),
        ('HR Use Only', {
            'fields': ('requisition_no', 'date_received')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'approved_at', 'created_at', 'updated_at')
        }),
    )


@admin.register(MRFApproval)
class MRFApprovalAdmin(admin.ModelAdmin):
    list_display = ['mrf', 'level', 'approver', 'action', 'created_at']
    list_filter = ['action', 'level']
    search_fields = ['mrf__requisition_no', 'approver__name']
    readonly_fields = ['created_at']


@admin.register(MRFRevision)
class MRFRevisionAdmin(admin.ModelAdmin):
    list_display = ['mrf', 'revised_by', 'created_at']
    search_fields = ['mrf__requisition_no', 'revised_by__name']
    readonly_fields = ['created_at']
