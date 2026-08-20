# onboarding/utils/onboarding_tasks.py

import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from jobs.models import JobApplication
from bgv.models import CandidateBGV
from .zoho_manageengine import ManageEngineClient
from .notifications import notify_candidate, notify_internal
from .task_generation import create_milestone_tasks, create_task
from .esign_tasks import generate_esign_documents, send_documents_for_esign, send_esign_reminders

logger = logging.getLogger(__name__)

def daily_onboarding_check():
    """
    Daily task to scan all candidates in 'offer_accepted', 'docs_pending', 'joining_pending' or 'joined' status,
    and trigger actions + auto-generate OnboardingTask records based on (joining_date - today).
    """
    logger.info("Running daily_onboarding_check...")

    today = timezone.now().date()

    # We only care about active applications that have a joining date and have accepted the offer.
    # Exclude candidates who have completed onboarding or are rejected/withdrawn.
    active_statuses = [
        "offer_accepted", "docs_pending", "docs_uploaded",
        "joining_pending", "joined", "docs_approved"
    ]

    candidates = JobApplication.objects.filter(
        is_active=True,
        status__in=active_statuses,
        joining_date__isnull=False,
        # Note: we intentionally do NOT filter out is_escalated=True here.
        # Escalated candidates must still receive D30/D45/D90 notifications.
    )

    me_client = ManageEngineClient()

    for app in candidates:
        if getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False):
            # Test Mode: Each milestone is exactly 1 minute apart.
            # minute 0 → DOJ - 15
            # minute 1 → DOJ -  7
            # minute 2 → DOJ -  2
            # minute 3 → DOJ    0
            # minute 4 → DOJ +  1
            # minute 5 → DOJ +  7
            # minute 6 → DOJ + 30
            # minute 7 → DOJ + 45
            # minute 8 → DOJ + 90
            _DEBUG_MINUTE_MAP = {0: 15, 1: 7, 2: 2, 3: 0, 4: -1, 5: -7, 6: -30, 7: -45, 8: -90}
            minutes_since_creation = int((timezone.now() - app.created_at).total_seconds() / 60)
            days_until_joining = _DEBUG_MINUTE_MAP.get(minutes_since_creation, 999)
            logger.debug(f"[DEBUG MODE] Candidate {app.candidate_name}: minutes_since_creation={minutes_since_creation}, mapped_days_until_joining={days_until_joining}")
        else:
            days_until_joining = (app.joining_date - today).days if app.joining_date else 999

        # ── DOJ - 15 Days ───────────────────────────────────────
        if days_until_joining <= 15 and not getattr(app, 'is_doj_minus_15_triggered', False) and app.status != "joined":
            logger.info(f"DOJ - 15 for candidate {app.candidate_name}. Updating ME ticket.")
            if app.it_ticket_ref:
                update_payload = {} # You can add specific custom fields here for procurement
                note = f"DOJ is in 15 days ({app.joining_date}). Please procure laptop."
                if app.job.job_type != 'work_from_office':
                    note += " (Remote joiner: VPN setup task required)."
                me_client.update_ticket(app.it_ticket_ref, update_payload, note=note)

            # Send Email to IT Team
            notify_internal(app, "doj_minus_15_it_team")
            create_milestone_tasks(app, "DOJ_MINUS_15", app.joining_date)
            app.is_doj_minus_15_triggered = True
            app.save(update_fields=['is_doj_minus_15_triggered'])
            app.refresh_from_db(fields=['is_doj_minus_7_triggered', 'is_doj_minus_2_triggered'])

        # ── DOJ - 7 Days ────────────────────────────────────────
        if days_until_joining <= 7 and not app.is_doj_minus_7_triggered and app.status != "joined":
            logger.info(f"DOJ - 7 for candidate {app.candidate_name}.")
            if app.job.job_type == 'work_from_office':
                notify_internal(app, "doj_minus_7_hod")
                notify_internal(app, "doj_minus_7_admin")
            else:
                if app.it_ticket_ref:
                    note = f"DOJ is in 7 days ({app.joining_date}). Remote joiner. Please arrange for laptop dispatch."
                    me_client.update_ticket(app.it_ticket_ref, {}, note=note)

            create_milestone_tasks(app, "DOJ_MINUS_7", app.joining_date)
            app.is_doj_minus_7_triggered = True
            app.save(update_fields=['is_doj_minus_7_triggered'])
            app.refresh_from_db(fields=['is_doj_minus_2_triggered'])

        # ── DOJ - 2 Days ────────────────────────────────────────
        if days_until_joining <= 2 and not app.is_doj_minus_2_triggered and app.status != "joined":
            logger.info(f"DOJ - 2 for candidate {app.candidate_name}. Welcome Email.")
            notify_candidate(app, "welcome_joining", cc=[])

            if app.it_ticket_ref and app.job.job_type != 'work_from_office':
                me_client.update_ticket(app.it_ticket_ref, {}, note="DOJ is in 2 days. Finalize VPN/dispatch tasks.")
            
            app.is_doj_minus_2_triggered = True
            app.save(update_fields=['is_doj_minus_2_triggered'])

        # ── DOJ 0 — Statutory docs + Zoho Sign packet ────────────
        # Diagram: released on "report joined". If your "report joined" action is a
        # separate manual endpoint, call generate_esign_documents()/send_documents_for_esign()
        # from there instead and drop this block. Left here as a same-day fallback so the
        # packet still goes out even if that manual step is skipped/delayed.
        # NOTE: generate_esign_documents() creates the tracking rows + raises "upload file"
        # tasks for HR; send_documents_for_esign() only sends docs that already have a
        # source_file. If HR hasn't uploaded anything yet, this fires but sends nothing —
        # it'll pick up uploaded files on a later cron pass since is_esign_packet_generated
        # only gates re-creating the rows, not re-sending.
        if days_until_joining <= 0:
            is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
            # In debug simulation the status stays 'joining_pending'; bypass the joined gate
            # so the simulation can proceed past DOJ 0.
            if (app.status == "joined" or is_debug) and not getattr(app, 'is_esign_packet_generated', False):
                logger.info(f"DOJ 0 for candidate {app.candidate_name}. Generating esign doc records.")
                generate_esign_documents(app)
                app.is_esign_packet_generated = True
                app.save(update_fields=['is_esign_packet_generated'])

            # Always attempt sending — catches docs HR uploaded after DOJ 0 fired.
            # In debug mode we skip the real Zoho API call.
            if getattr(app, 'is_esign_packet_generated', False) and not is_debug:
                send_documents_for_esign(app)

        # ── DOJ + 1 Day — esign reminder (real implementation, was a stub) ─────
        if days_until_joining <= -1:
            is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
            # In debug mode skip the Zoho/esign check so simulation continues
            if is_debug:
                logger.info(f"[DEBUG] DOJ + 1 esign reminder step passed for {app.candidate_name}.")
            elif getattr(app, 'is_esign_packet_generated', False) and not getattr(app, 'is_esign_reminder_sent', False):
                logger.info(f"DOJ + 1 for candidate {app.candidate_name}. Checking for unsigned esign docs.")
                send_esign_reminders(app)
                app.is_esign_reminder_sent = True
                app.save(update_fields=['is_esign_reminder_sent'])

        # ── DOJ + 5 Days (Document Verification) ────────────────
        if days_until_joining <= -5 and not getattr(app, 'is_d5_verification_sent', False):
            logger.info(f"DOJ + 5 for candidate {app.candidate_name}. Sending document verification email.")
            notify_candidate(app, "d5_document_verification", cc=[])
            app.is_d5_verification_sent = True
            app.save(update_fields=['is_d5_verification_sent'])

        # ── DOJ + 7 Days (Escalation Check) ─────────────────────
        if days_until_joining <= -7:
            logger.info(f"DOJ + 7 for candidate {app.candidate_name}. Checking BGV status.")
            
            designation_name = app.job.mrf.designation.name.lower() if (
                hasattr(app, 'job') and app.job and
                hasattr(app.job, 'mrf') and app.job.mrf and
                app.job.mrf.designation
            ) else ""
            is_intern = 'intern' in designation_name
            is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)

            # In debug simulation, skip the real BGV lookup so is_escalated stays False
            # and downstream D30/D45/D90 milestones are not blocked.
            if not is_debug and not app.is_escalated and not is_intern:
                try:
                    bgv = CandidateBGV.objects.get(candidate=app)
                    if bgv.status not in ['clear', 'verified']:
                        app.is_escalated = True
                        app.save(update_fields=['is_escalated'])
                        notify_internal(app, "bgv_escalation")
                except CandidateBGV.DoesNotExist:
                    app.is_escalated = True
                    app.save(update_fields=['is_escalated'])
                    notify_internal(app, "bgv_escalation")

            create_milestone_tasks(app, "DOJ_PLUS_7_BGV", app.joining_date)

        days_past = 0
        if days_until_joining < 0:
            days_past = abs(days_until_joining)

        # ── DOJ + 30 Days ─────────────────────────────────────────
        if days_past >= 30 and not getattr(app, 'is_d30_survey_sent', False):
            logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Sending 30-day candidate survey reminder.")
            notify_candidate(app, "satisfaction_survey", cc=[])
            app.is_d30_survey_sent = True
            app.save(update_fields=['is_d30_survey_sent'])

        if days_past >= 30 and not getattr(app, 'is_hod_survey_filled', False):
            logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Sending HOD survey reminder.")
            is_senior = False
            try:
                designation_name = app.job.mrf.designation.name.lower() if (
                    hasattr(app, 'job') and app.job and
                    hasattr(app.job, 'mrf') and app.job.mrf and
                    app.job.mrf.designation
                ) else ""
                higher_keywords = [
                    'assistant manager', 'associate manager', 'manager',
                    'senior manager', 'associate vice president',
                    'director', 'vp', 'vice president', 'president',
                    'head', 'chief', 'lead', 'principal', 'avp'
                ]
                is_senior = any(kw in designation_name for kw in higher_keywords)
            except Exception as e:
                logger.warning(f"Could not determine seniority for {app.candidate_name}: {e}")

            hod_stage = "satisfaction_survey_hod_senior" if is_senior else "satisfaction_survey_hod_junior"
            notify_internal(app, hod_stage)
            app.is_hod_survey_filled = True
            app.save(update_fields=['is_hod_survey_filled'])

        # ── DOJ + 45 Days ───────────────────────
        if days_past >= 45 and not getattr(app, 'is_d45_call_scheduled', False):
            logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Check-in invite reminder (D45).")
            notify_internal(app, "schedule_checkin_call_reminder")
            app.d45_reminder_count = getattr(app, 'd45_reminder_count', 0) + 1
            save_fields = ['d45_reminder_count']
            if app.d45_reminder_count >= 5 and not getattr(app, 'is_d45_call_escalated', False):
                logger.warning(f"D45 escalation for {app.candidate_name}: {app.d45_reminder_count} reminders sent, call not scheduled.")
                notify_internal(app, "d45_call_not_scheduled_escalation")
                app.is_d45_call_escalated = True
                save_fields.append('is_d45_call_escalated')
            app.save(update_fields=save_fields)

        # ── DOJ + 90 Days ─────────────
        if days_past >= 90 and not getattr(app, 'is_d90_survey_sent', False):
            logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Sending 90-day survey + final review reminder.")
            notify_candidate(app, "d90_survey", cc=[])
            notify_internal(app, "schedule_final_review_reminder")
            app.d90_reminder_count = getattr(app, 'd90_reminder_count', 0) + 1
            d90_save_fields = ['d90_reminder_count']
            if app.d90_reminder_count >= 5 and not getattr(app, 'is_d90_call_escalated', False):
                logger.warning(f"D90 escalation for {app.candidate_name}: {app.d90_reminder_count} reminders sent, call not scheduled.")
                notify_internal(app, "d90_call_not_scheduled_escalation")
                app.is_d90_call_escalated = True
                d90_save_fields.append('is_d90_call_escalated')
            app.save(update_fields=d90_save_fields)

            try:
                from onboarding.models import SurveyResponse
                SurveyResponse.objects.get_or_create(
                    job_application=app,
                    survey_type='90_day_candidate',
                    defaults={
                        'respondent_name': app.candidate_name,
                        'respondent_email': getattr(app, 'work_email', None) or app.candidate_email,
                        'responses': {},
                    }
                )
            except Exception as survey_err:
                logger.warning(f"Could not create 90-day SurveyResponse record for {app.candidate_name}: {survey_err}")

            app.is_d90_survey_sent = True
            app.save(update_fields=['is_d90_survey_sent'])

        if days_past >= 90 and app.it_ticket_ref and not getattr(app, 'it_ticket_closed', False):
            logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Closing ManageEngine IT ticket.")
            if me_client.close_ticket(app.it_ticket_ref):
                app.it_ticket_closed = True
                app.save(update_fields=['it_ticket_closed'])

    return True


# ---------------------------------------------------------------------------
# Admin-action helper — mirrors the ONBOARDING_DEBUG_MINUTES branch exactly
# so the admin can replay the automated flow for selected candidates without
# affecting the live daily_onboarding_check cron.
# ---------------------------------------------------------------------------

def run_onboarding_check_for_candidate(app):
    """
    Run the full automated onboarding timeline for a single JobApplication,
    using their actual days until joining, to manually simulate/run what
    the cron job would do for them today.
    """
    logger.info(f"[ADMIN ACTION] Running onboarding check for: {app.candidate_name}")

    me_client = ManageEngineClient()
    joining_date = app.joining_date
    if not joining_date:
        logger.error(f"[ADMIN ACTION] Candidate {app.candidate_name} has no joining date.")
        return 999
        
    today = timezone.now().date()
    
    if getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False):
        _DEBUG_MINUTE_MAP = {0: 15, 1: 7, 2: 2, 3: 0, 4: -1, 5: -7, 6: -30, 7: -45, 8: -90}
        minutes_since_creation = int((timezone.now() - app.created_at).total_seconds() / 60)
        days_until_joining = _DEBUG_MINUTE_MAP.get(minutes_since_creation, 999)
        logger.debug(
            f"[ADMIN ACTION - DEBUG MODE] {app.candidate_name}: minutes_since_creation={minutes_since_creation}, mapped_days_until_joining={days_until_joining}"
        )
    else:
        days_until_joining = (joining_date - today).days
        logger.debug(
            f"[ADMIN ACTION] {app.candidate_name}: days_until_joining={days_until_joining}"
        )

    # ── DOJ - 15 Days ───────────────────────────────────────────────────────
    if days_until_joining <= 15 and not getattr(app, 'is_doj_minus_15_triggered', False) and app.status != "joined":
        logger.info(f"[ADMIN ACTION] DOJ - 15 for {app.candidate_name}. Updating ME ticket.")
        if app.it_ticket_ref:
            note = f"DOJ is in 15 days ({joining_date}). Please procure laptop."
            if app.job and app.job.job_type != 'work_from_office':
                note += " (Remote joiner: VPN setup task required)."
            me_client.update_ticket(app.it_ticket_ref, {}, note=note)
        notify_internal(app, "doj_minus_15_it_team")
        create_milestone_tasks(app, "DOJ_MINUS_15", joining_date)
        app.is_doj_minus_15_triggered = True
        app.save(update_fields=['is_doj_minus_15_triggered'])
        app.refresh_from_db(fields=['is_doj_minus_7_triggered', 'is_doj_minus_2_triggered'])

    # ── DOJ - 7 Days ────────────────────────────────────────────────────────
    if days_until_joining <= 7 and not getattr(app, 'is_doj_minus_7_triggered', False) and app.status != "joined":
        logger.info(f"[ADMIN ACTION] DOJ - 7 for {app.candidate_name}.")
        if app.job and app.job.job_type == 'work_from_office':
            notify_internal(app, "doj_minus_7_hod")
            notify_internal(app, "doj_minus_7_admin")
        # else:
            # if app.it_ticket_ref:
            #     note = f"DOJ is in 7 days ({joining_date}). Remote joiner. Please arrange laptop dispatch."
            # me_client.update_ticket(app.it_ticket_ref, {}, note=note)
        create_milestone_tasks(app, "DOJ_MINUS_7", joining_date)
        app.is_doj_minus_7_triggered = True
        app.save(update_fields=['is_doj_minus_7_triggered'])
        app.refresh_from_db(fields=['is_doj_minus_2_triggered'])

    # ── DOJ - 2 Days ────────────────────────────────────────────────────────
    if days_until_joining <= 2 and not getattr(app, 'is_doj_minus_2_triggered', False) and app.status != "joined":
        logger.info(f"[ADMIN ACTION] DOJ - 2 for {app.candidate_name}. Welcome email.")
        
        location = "Gurugram"
        try:
            from onboarding.models import ApprovalNote
            an = ApprovalNote.objects.filter(candidate=app, status='approved').last()
            if an and an.payload.get('mrf', {}).get('location'):
                location = an.payload['mrf']['location']
            elif app.job and hasattr(app.job, 'mrf') and app.job.mrf.location:
                location = app.job.mrf.location
        except Exception as e:
            logger.error(f"Failed to fetch location for welcome email: {e}")
            
        notify_candidate(app, "welcome_joining", cc=[], extra_context={'location': location})
        # if app.it_ticket_ref and app.job and app.job.job_type != 'work_from_office':
            # me_client.update_ticket(app.it_ticket_ref, {}, note="DOJ is in 2 days. Finalize VPN/dispatch tasks.")
            
        app.is_doj_minus_2_triggered = True
        app.save(update_fields=['is_doj_minus_2_triggered'])

    # ── DOJ 0 — Statutory docs + e-sign packet ─────────────────────────────
    if days_until_joining <= 0 and not getattr(app, 'is_doj_0_triggered', False):
        is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
        if (app.status == "joined" or is_debug) and not getattr(app, 'is_esign_packet_generated', False):
            logger.info(f"[ADMIN ACTION] DOJ 0 for {app.candidate_name}. Generating esign doc records.")
            generate_esign_documents(app)
            # app.is_esign_packet_generated = True
            # app.save(update_fields=['is_esign_packet_generated'])
            # create_milestone_tasks(app, "DOJ_0_DOCS", joining_date)

        if getattr(app, 'is_esign_packet_generated', False) and not is_debug:
            send_documents_for_esign(app)
        app.is_doj_0_triggered = True
        app.save(update_fields=['is_doj_0_triggered'])

    # ── DOJ + 1 Day — esign reminder ────────────────────────────────────────
    if days_until_joining <= -1:
        is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
        if is_debug:
            logger.info(f"[ADMIN ACTION - DEBUG] DOJ + 1 esign reminder step passed for {app.candidate_name}.")
        elif getattr(app, 'is_esign_packet_generated', False) and not getattr(app, 'is_esign_reminder_sent', False):
            logger.info(f"[ADMIN ACTION] DOJ + 1 for {app.candidate_name}. Checking unsigned esign docs.")
            send_esign_reminders(app)
            app.is_esign_reminder_sent = True
            app.save(update_fields=['is_esign_reminder_sent'])
            create_milestone_tasks(app, "DOJ_PLUS_1_ESIGN_REMINDER", joining_date)

    # ── DOJ + 5 Days — Document Verification ────────────────────────────────
    if days_until_joining <= -5 and not getattr(app, 'is_d5_verification_sent', False):
        logger.info(f"[ADMIN ACTION] DOJ + 5 for {app.candidate_name}. Sending document verification email.")
        notify_candidate(app, "d5_document_verification", cc=[])
        app.is_d5_verification_sent = True
        app.save(update_fields=['is_d5_verification_sent'])

    # ── DOJ + 7 Days — BGV check ────────────────────────────────────────────
    if days_until_joining <= -7 and not getattr(app, 'is_doj_7_triggered', False):
        logger.info(f"[ADMIN ACTION] DOJ + 7 for {app.candidate_name}. Checking BGV status.")
        designation_name = app.job.mrf.designation.name.lower() if (
            app.job and app.job.mrf and app.job.mrf.designation
        ) else ""
        is_intern = 'intern' in designation_name
        is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)

        if not is_debug and not app.is_escalated and not is_intern:
            try:
                bgv = CandidateBGV.objects.get(candidate=app)
                if bgv.status not in ['clear', 'verified']:
                    app.is_escalated = True
                    app.save(update_fields=['is_escalated'])
                    notify_internal(app, "bgv_escalation")
            except CandidateBGV.DoesNotExist:
                app.is_escalated = True
                app.save(update_fields=['is_escalated'])
                notify_internal(app, "bgv_escalation",cc=['zafiya.mallick@knowcraft.in'])
        create_milestone_tasks(app, "DOJ_PLUS_7_BGV", joining_date)
        app.is_doj_7_triggered = True
        app.save(update_fields=['is_doj_7_triggered'])

    days_past = abs(days_until_joining) if days_until_joining < 0 else 0

    # ── DOJ + 30 Days ───────────────────────────────────────────────────────
    if days_past >= 30 and not getattr(app, 'is_d30_survey_sent', False):
        logger.info(f"[ADMIN ACTION] DOJ + {days_past} for {app.candidate_name}. Sending 30-day survey.")
        notify_candidate(app, "satisfaction_survey", cc=[])
        app.is_d30_survey_sent = True
        app.save(update_fields=['is_d30_survey_sent'])
        # create_milestone_tasks(app, "DOJ_PLUS_30_SURVEY", joining_date)

    if days_past >= 30 and not getattr(app, 'is_hod_survey_filled', False):
        logger.info(f"[ADMIN ACTION] DOJ + {days_past} for {app.candidate_name}. Sending HOD survey.")
        is_senior = False
        try:
            designation_name = app.job.mrf.designation.name.lower() if (
                app.job and app.job.mrf and app.job.mrf.designation
            ) else ""
            higher_keywords = [
                'assistant manager', 'associate manager', 'manager',
                'senior manager', 'associate vice president',
                'director', 'vp', 'vice president', 'president',
                'head', 'chief', 'lead', 'principal', 'avp'
            ]
            is_senior = any(kw in designation_name for kw in higher_keywords)
        except Exception as e:
            logger.warning(f"[ADMIN ACTION] Could not determine seniority for {app.candidate_name}: {e}")
        hod_stage = "satisfaction_survey_hod_senior" if is_senior else "satisfaction_survey_hod_junior"
        notify_internal(app, hod_stage)
    
    # ── DOJ + 45 Days ───────────────────────────────────────────────────────
    if days_past >= 45 and not getattr(app, 'is_d45_call_scheduled', False):
        logger.info(f"[ADMIN ACTION] DOJ + {days_past} for {app.candidate_name}. D45 check-in reminder.")
        notify_internal(app, "schedule_checkin_call_reminder")
        app.is_doj_45_triggered = True
        app.save(update_fields=['is_doj_45_triggered'])
    
    # ── DOJ + 90 Days ───────────────────────────────────────────────────────
    if days_past >= 90 and not getattr(app, 'is_d90_survey_sent', False):
        logger.info(f"[ADMIN ACTION] DOJ + {days_past} for {app.candidate_name}. Sending 90-day survey.")
        notify_candidate(app, "d90_survey", cc=[])
        notify_internal(app, "schedule_final_review_reminder")
        try:
            from onboarding.models import SurveyResponse
            SurveyResponse.objects.get_or_create(
                job_application=app,
                survey_type='90_day_candidate',
                defaults={
                    'respondent_name': app.candidate_name,
                    'respondent_email': getattr(app, 'work_email', None) or app.candidate_email,
                    'responses': {},
                }
            )
        except Exception as survey_err:
            logger.warning(f"[ADMIN ACTION] Could not create 90-day SurveyResponse for {app.candidate_name}: {survey_err}")
        app.is_d90_survey_sent = True
        app.save(update_fields=['is_d90_survey_sent'])
        create_milestone_tasks(app, "DOJ_PLUS_90_FINAL", joining_date)

    if days_past >= 90 and app.it_ticket_ref and not getattr(app, 'it_ticket_closed', False):
        logger.info(f"[ADMIN ACTION] DOJ + {days_past} for {app.candidate_name}. Closing ME IT ticket.")
        if me_client.close_ticket(app.it_ticket_ref):
            app.it_ticket_closed = True
            app.save(update_fields=['it_ticket_closed'])

    logger.info(f"[ADMIN ACTION] Completed onboarding check for: {app.candidate_name}")
    return days_until_joining
