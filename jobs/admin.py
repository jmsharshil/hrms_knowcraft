from django.contrib import admin
from .models import Job, JobAssignmentHistory, JobApplication, ReferralApplication, Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'candidate_name', 'candidate_email', 'job', 'source', 'created_at'
    ]
    list_filter = ['source', 'created_at']
    search_fields = ['candidate_name', 'candidate_email', 'candidate_phone', 'job__job_title']
    readonly_fields = ['id']

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    filter_horizontal = ('assigned_consultancies', 'assigned_internal_hrs')
    
    list_display = [
        'job_title', 'department', 'location', 'no_of_positions',
        'status', 'previous_status', 'priority', 'is_active',
        'created_at','positions_filled'
    ]
    list_filter = [
        'status', 'priority', 'is_active', 'visible_to_consultancy',
        'department', 'location', 'created_at'
    ]
    search_fields = [
        'job_title', 'mrf__requisition_no', 'location',
        'skills_competencies', 'key_responsibility'
    ]
    # readonly_fields = [
    #     'id', 'created_at', 'updated_at', 'assigned_at',
    #     'filled_at', 'posted_by', 'assigned_by', 'filled_by_user'
    # ]
    readonly_fields = [
        'id'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id', 'mrf', 'job_title', 'department', 'designation',
                'location', 'no_of_positions','positions_filled'
            )
        }),
        ('Job Requirements', {
            'fields': (
                'key_responsibility', 'required_qualifications',
                'experience_range', 'skills_competencies', 'salary_range'
            )
        }),
        ('Status & Priority', {
            'fields': (
                'status', 'previous_status', 'priority', 'is_active', 'visible_to_consultancy',
                'expected_closure_date'
            )
        }),
        ('Assignment Details', {
            'fields': (
                'assigned_consultancies', 'assigned_internal_hrs', 'assigned_at', 'assigned_by'
            )
        }),
        # ('Closure Details', {
        #     'fields': (
        #         'filled_by', 'filled_at', 'filled_by_user', 'closure_notes'
        #     )
        # }),
        ('Tracking', {
            'fields': (
                'posted_by', 'company', 'created_at', 'updated_at'
            )
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'department', 'designation', 'mrf',
            'posted_by', 'company'
        )


@admin.register(JobAssignmentHistory)
class JobAssignmentHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'job', 'action', 'consultancy', 'performed_by', 'created_at'
    ]
    list_filter = ['action', 'created_at']
    search_fields = [
        'job__job_title', 'consultancy__full_name', 'performed_by__full_name',
        'notes'
    ]
    readonly_fields = ['id']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'job', 'consultancy', 'performed_by'
        )


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'candidate_name', 'candidate_email', 'job', 'status',
        'joining_date', 'offer_accepted_date',
        'source', 'submitted_by', 'created_at'
    ]
    list_filter = ['status', 'source', 'created_at','bgv_status']
    search_fields = [
        'candidate_name', 'candidate_email', 'candidate_phone',
        'job__job_title', 'notes'
    ]
    readonly_fields = ['id']
    fieldsets = (
        ('Candidate Information', {
            'fields': (
                'id', 'candidate_name', 'candidate_email', 'candidate_phone',
                'resume', 'experience_years'
            )
        }),
        ('Job & Status', {
            'fields': (
                'job', 'status', 'joining_date', 'offer_accepted_date', 'source', 'submitted_by', 'bgv_status'
            )
        }),
        ('Compensation', {
            'fields': (
                'current_ctc', 'expected_ctc', 'notice_period'
            )
        }),
        ('Additional Information', {
            'fields': (
                'notes', 'created_at', 'updated_at'
            )
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'job', 'job__department', 'submitted_by'
        )
    
@admin.register(ReferralApplication)
class ReferralApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'referral_name', 'referral_email', 'referral_emp_code',
        'position_title', 'created_at'
    ]
    list_filter = ['created_at', 'referral_department', 'referral_designation']
    search_fields = [
        'referral_name', 'referral_email', 'referral_emp_code',
        'position_title', 'notes'
    ]
    readonly_fields = ['id', 'file_size', 'original_filename']
    
    fieldsets = (
        ('Referral Information', {
            'fields': (
                'id', 'referral_name', 'referral_email', 'referral_emp_code',
                'referral_designation', 'referral_department'
            )
        }),
        ('Position Details', {
            'fields': (
                'position_title',
            )
        }),
        ('Resume', {
            'fields': (
                'resume', 'original_filename', 'file_size'
            )
        }),
        ('Additional Notes', {
            'fields': (
                'notes', 'created_at', 'updated_at'
            )
        }),
    )