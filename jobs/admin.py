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
        'candidate_name', 'candidate_email', 'candidate_phone',
        'job', 'status', 'bgv_status', 'source',
        'experience_years', 'joining_date', 'offer_accepted_date',
        'is_active', 'is_satisfaction_survey_filled', 'is_hod_survey_filled',
        'is_d45_call_scheduled', 'is_d90_call_scheduled', 'submitted_by', 'created_at',
    ]
    list_filter = [
        'status', 'bgv_status', 'source', 'round_name',
        'is_active', 'is_duplicate', 'is_shortlisted',
        'is_selected', 'is_approved', 'is_rejected',
        'is_satisfaction_survey_filled', 'is_hod_survey_filled',
        'is_d45_call_scheduled', 'is_d90_call_scheduled',
        'created_at',
    ]
    search_fields = [
        'candidate_name', 'candidate_email', 'candidate_phone',
        'job__job_title', 'notes', 'current_employer',
        'referral_name', 'referral_email', 'referral_emp_code',
        'interviewer_name',
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at',
        'consolidated_feedback_avg', 'match_score',
        'no_show_count', 'reschedule_count',
    ]
    filter_horizontal = ()
    fieldsets = (
        ('Candidate Information', {
            'fields': (
                'id',
                'candidate_name', 'candidate_email', 'candidate_phone',
                'location', 'linkedin_url', 'portfolio_url',
                'current_employer', 'availibility',
                'skill', 'education',
                'cover_letter',
            )
        }),
        # ── 2. Job & Application ──────────────────────────────────
        ('Job & Application', {
            'fields': (
                'job', 'application_link',
                'source', 'submitted_by',
            )
        }),
        # ── 3. Pipeline Status ───────────────────────────────────
        ('Status & Flags', {
            'fields': (
                'status', 'bgv_status',
                'is_active', 'is_duplicate', 'is_shortlisted',
                'is_selected', 'is_approved', 'is_rejected',
                'joining_date', 'offer_accepted_date',
                'rejection_reason', 'offer_decline_reason',
                'slot_link', 'inperson_link',
            )
        }),
        # ── 3.5. Post Joining & Onboarding ────────────────────────────
        ('Post Joining & Onboarding', {
            'fields': (
                'it_ticket_ref', 'emp_account_active', 'work_email',
                'technical_buddy_name', 'technical_buddy_email', 'cultural_buddy_name', 'cultural_buddy_email', 'is_escalated', 
                'is_satisfaction_survey_filled', 'is_hod_survey_filled',
                'is_d45_call_scheduled', 'is_d90_call_scheduled'
            )
        }),
        # ── 4. Compensation ───────────────────────────────────────
        ('Compensation', {
            'fields': (
                'experience_years', 'relevant_experience_years',
                'current_ctc', 'expected_ctc', 'notice_period',
            )
        }),
        # ── 5. Interview Details ──────────────────────────────────
        ('Interview Details', {
            'fields': (
                'round_name',
                'interview_scheduled_at', 'interview_end_at',
                'interviewer_name',
                'interview_link', 'feedback_link',
                'no_show_count', 'reschedule_count',
            )
        }),
        # ── 6. Referral ───────────────────────────────────────────
        ('Referral Details', {
            'classes': ('collapse',),
            'fields': (
                'referral_name', 'referral_email', 'referral_phone',
                'referral_emp_code', 'referral_designation', 'referral_department',
            )
        }),
        # ── 7. Resume & AI Scoring ────────────────────────────────
        ('Resume & Files', {
            'fields': (
                'resume', 'original_filename', 'file_size',
                'resume_report', 'match_score',
            )
        }),
        # ── 8. Ratings & Feedback ─────────────────────────────────
        ('Ratings & Feedback', {
            'classes': ('collapse',),
            'fields': (
                'rating', 'consolidated_feedback_avg',
                'candidate_history',
            )
        }),
        # ── 9. Timestamps & Notes ─────────────────────────────────
        ('Tracking & Notes', {
            'fields': (
                'notes', 'created_at', 'updated_at'
            )
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'job', 'job__department', 'job__mrf',
            'submitted_by', 'application_link',
        )

    actions = ['send_90_day_survey', 'simulate_onboarding_process']

    def send_90_day_survey(self, request, queryset):
        """Send 90-day survey form link to selected candidates. Responses saved to SurveyResponse model in DB."""
        from onboarding.utils.notifications import notify_candidate
        count = 0
        for application in queryset:
            if not getattr(application, 'is_satisfaction_survey_filled', False):
                success = notify_candidate(
                    application, 
                    "d90_survey", 
                    cc=[]
                )
                if success:
                    count += 1
        self.message_user(request, f"Successfully sent 90-day survey form to {count} candidate(s). Responses will be automatically saved to the database (SurveyResponse model) when submitted via the form.")
    send_90_day_survey.short_description = "Send 90 Day Survey Form (saves responses to DB)"

    def simulate_onboarding_process(self, request, queryset):
        import time
        from onboarding.utils.engine import automation_engine
        from onboarding.utils.task_generation import create_milestone_tasks
        
        count = 0
        for application in queryset:
            # First, make sure the candidate is joining_pending
            if application.status != 'joining_pending':
                application.status = 'joining_pending'
                application.save(update_fields=['status'])
            
            # Now simulate transitions
            states_to_simulate = [
                'joined'
            ]
            
            old_state = 'joining_pending'
            for new_state in states_to_simulate:
                print(f"[DEBUG SIMULATION] Moving {application.candidate_name} from {old_state} -> {new_state}")
                automation_engine(application, old_state, new_state)
                old_state = new_state
                time.sleep(2)
                
            # Now simulate milestone task generations based on joining_date (if None, use today)
            joining_date = application.joining_date
            if not joining_date:
                from django.utils import timezone
                joining_date = timezone.now().date()
            
            milestones = [
                "DOJ_MINUS_15",
                "DOJ_MINUS_7",
                "DOJ_0_DOCS",
                "DOJ_PLUS_1_ESIGN_REMINDER",
                "DOJ_PLUS_7_BGV",
                "DOJ_PLUS_30_SURVEY",
                "DOJ_PLUS_45_CHECKIN",
                "DOJ_PLUS_90_FINAL"
            ]
            for ms in milestones:
                print(f"[DEBUG SIMULATION] Generating tasks for milestone: {ms}")
                create_milestone_tasks(application, ms, joining_date)
                time.sleep(1)
                
            count += 1
            
        self.message_user(request, f"Successfully simulated onboarding process for {count} candidate(s). Check server logs for details.")
    simulate_onboarding_process.short_description = "Simulate Onboarding Process (Realtime Emails & Tasks)"
    
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