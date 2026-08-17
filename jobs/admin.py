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

    actions = ['send_90_day_survey', 'simulate_onboarding_process', 'initiate_onboarding_process', 'trigger_automated_onboarding_tasks']

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

    def initiate_onboarding_process(self, request, queryset):
        from onboarding.utils.engine import automation_engine
        
        count = 0
        for application in queryset:
            if application.status != 'joining_pending':
                old_status = application.status
                application.status = 'joining_pending'
                application.save(update_fields=['status'])
                
                print(f"[ONBOARDING INITIATED] Moving {application.candidate_name} from {old_status} -> joining_pending")
                automation_engine(application, old_status, 'joining_pending')
                count += 1
                
        self.message_user(request, f"Successfully initiated onboarding for {count} candidate(s).")
    initiate_onboarding_process.short_description = "Initiate Onboarding Process (Sets to Joining Pending)"

    def trigger_automated_onboarding_tasks(self, request, queryset):
        """
        Trigger the automated onboarding tasks flow for selected candidates.
        Runs in a background daemon thread so the admin request returns immediately
        without hitting a 504 timeout.
        Uses the same minutes-since-creation timeline as ONBOARDING_DEBUG_MINUTES = True.
        The live daily_onboarding_check cron is NOT affected.
        """
        import threading
        from onboarding.utils.onboarding_tasks import run_onboarding_check_for_candidate

        # Freeze the queryset into a plain list so the thread doesn't
        # hold a live DB cursor after the request cycle ends.
        applications = list(queryset)
        skipped = [a.candidate_name for a in applications if not a.joining_date]
        to_process = [a for a in applications if a.joining_date]

        def _run():
            for application in to_process:
                try:
                    days_mapped = run_onboarding_check_for_candidate(application)
                    print(
                        f"[BG TRIGGER] {application.candidate_name} → mapped day {days_mapped}. "
                        f"Check server logs for details."
                    )
                except Exception as e:
                    print(f"[BG TRIGGER] Error processing {application.candidate_name}: {e}")

        if to_process:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            self.message_user(
                request,
                f"Onboarding task check started in background for "
                f"{len(to_process)} candidate(s): "
                f"{', '.join(a.candidate_name for a in to_process)}. "
                f"Check server logs for progress."
            )
        if skipped:
            self.message_user(
                request,
                f"Skipped (no joining date set): {', '.join(skipped)}.",
                level='warning',
            )
    trigger_automated_onboarding_tasks.short_description = "Trigger Automated Onboarding Tasks (Background, Debug-Mode Timeline)"


    def simulate_onboarding_process(self, request, queryset):
        """
        Runs the FULL onboarding timeline for selected candidates in proper sequential
        flow — milestone by milestone — in a background daemon thread so the admin
        request returns immediately without hitting a 504 timeout.

        Timeline (1 minute per milestone, mirrors the new _DEBUG_MINUTE_MAP):
          minute 0  →  DOJ - 15  (IT team email + tasks)
          minute 1  →  DOJ -  7  (HOD/Admin email + tasks)
          minute 2  →  DOJ -  2  (Welcome email)
          minute 3  →  DOJ   0   (E-sign docs generated, status must be 'joined')
          minute 4  →  DOJ +  1  (E-sign reminder)
          minute 5  →  DOJ +  7  (BGV escalation check)
          minute 6  →  DOJ + 30  (30-day survey + HOD survey)
          minute 7  →  DOJ + 45  (45-day check-in reminder)
          minute 8  →  DOJ + 90  (90-day survey + final review + close IT ticket)
        """
        import threading
        import datetime as dt
        import time
        from django.utils import timezone
        from onboarding.utils.engine import automation_engine
        from onboarding.utils.onboarding_tasks import run_onboarding_check_for_candidate

        # Milestone minute-marks (aligned with the new _DEBUG_MINUTE_MAP in onboarding_tasks.py)
        MILESTONE_MINUTES = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        MILESTONE_LABELS = {
            0: "DOJ - 15", 1: "DOJ -  7", 2: "DOJ -  2",
            3: "DOJ   0",  4: "DOJ +  1", 5: "DOJ +  7",
            6: "DOJ + 30", 7: "DOJ + 45", 8: "DOJ + 90",
        }

        # Freeze queryset — thread must not hold a live DB cursor
        applications = list(queryset)
        skipped = [a.candidate_name for a in applications if not a.joining_date]
        to_process = [a for a in applications if a.joining_date]

        def _run():
            for application in to_process:
                app_name = application.candidate_name

                # ── 1. Transition to joining_pending → joined ──────────────
                if application.status not in ('joining_pending', 'joined'):
                    old_status = application.status
                    application.status = 'joining_pending'
                    application.save(update_fields=['status'])
                    print(f"[FULL SIM] {app_name}: {old_status} → joining_pending")
                    try:
                        automation_engine(application, old_status, 'joining_pending')
                    except Exception as exc:
                        print(f"[FULL SIM] automation_engine error (→joining_pending): {exc}")
                    time.sleep(2)

                if application.status == 'joining_pending':
                    application.status = 'joined'
                    application.save(update_fields=['status'])
                    print(f"[FULL SIM] {app_name}: joining_pending → joined")
                    try:
                        automation_engine(application, 'joining_pending', 'joined')
                    except Exception as exc:
                        print(f"[FULL SIM] automation_engine error (→joined): {exc}")
                    time.sleep(2)

                # Reload fresh from DB so all flag values are current
                application.refresh_from_db()

                # ── 2. Walk through every milestone in order ───────────────
                original_created_at = application.created_at

                for minutes in MILESTONE_MINUTES:
                    # Sleep 1 real second per simulated minute to space out
                    # the milestones — adjust to taste (e.g. 60 for real minutes)
                    if minutes > 0:
                        time.sleep(60)  # 1 real minute between each milestone

                    # Fake created_at so run_onboarding_check_for_candidate
                    # sees exactly `minutes` elapsed minutes.
                    application.created_at = timezone.now() - dt.timedelta(minutes=minutes)

                    label = MILESTONE_LABELS.get(minutes, f"minute {minutes}")
                    print(f"[FULL SIM] {app_name} → {label} (created_at faked to -{minutes}min)")

                    try:
                        run_onboarding_check_for_candidate(application)
                    except Exception as exc:
                        print(f"[FULL SIM] Error at {label} for {app_name}: {exc}")

                    # Sync guard flags from DB so the next milestone respects them
                    db_app = application.__class__.objects.get(pk=application.pk)
                    for flag in [
                        'is_esign_packet_generated', 'is_esign_reminder_sent',
                        'is_escalated', 'is_d30_survey_sent', 'is_hod_survey_filled',
                        'is_d45_call_scheduled', 'is_d90_survey_sent', 'it_ticket_closed',
                    ]:
                        if hasattr(db_app, flag):
                            setattr(application, flag, getattr(db_app, flag))

                # Restore real created_at in memory (never persisted to DB)
                application.created_at = original_created_at
                print(f"[FULL SIM] Completed full timeline for {app_name}")

        if to_process:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            self.message_user(
                request,
                f"Full onboarding simulation started in background for "
                f"{len(to_process)} candidate(s): "
                f"{', '.join(a.candidate_name for a in to_process)}. "
                f"Each milestone runs 1 minute apart (~{len(MILESTONE_MINUTES)} min total). "
                f"Check server logs for live progress."
            )
        if skipped:
            self.message_user(
                request,
                f"Skipped (no joining_date): {', '.join(skipped)}",
                level='warning',
            )

    simulate_onboarding_process.short_description = "Simulate Full Onboarding Flow (Background, 1-min milestones)"
    
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