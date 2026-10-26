# onboarding/utils/onboarding_tasks.py

import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from jobs.models import JobApplication
from bgv.models import CandidateBGV
# from .zoho_manageengine import ManageEngineClient
from .notifications import notify_candidate, notify_internal, send_welcome_email
from .task_generation import create_milestone_tasks, create_task
from .esign_tasks import generate_esign_documents, send_documents_for_esign, send_esign_reminders

logger = logging.getLogger(__name__)

BGV_COMPLETED_STATUSES = [
    'clear', 'verified', 'completed', 'bgv_completed', 'closed', 'unable_to_verify'
]

DEBUG_ONBOARDING_MILESTONES = (
    (0, 15),
    (1, 7),
    (2, 2),
    (3, 0),
    (4, -1),   # Day 2: HR Handbook & DOJ+1 esign reminder
    (5, -2),   # Day 3: Culture & Values Handbook
    (6, -3),   # Day 4: POSH Policy & Guidelines
    (7, -4),   # Day 5: Chatbot User Manual
    (8, -5),   # Day 6: KAI Mascot + D5 verification & Undertaking signoff
    (9, -7),   # DOJ + 7
    (10, -30), # DOJ + 30
    (11, -45), # DOJ + 45
    (12, -90), # DOJ + 90
)


def remind_call_owners_for_missing_materials(now=None):
    from onboarding.models import EmailLog, OnboardingCall
    from onboarding.utils.sender import send_email

    now = now or timezone.now()
    calls = OnboardingCall.objects.filter(
        end_time__isnull=False,
        end_time__lte=now,
    ).select_related("job_application")

    for call in calls:
        missing_materials = []
        if not call.mom_notes.strip():
            missing_materials.append("MOM notes")
        if not call.transcript_file:
            missing_materials.append("the call transcript")
        owner_email = (call.organizer_email or "").strip()
        if not missing_materials or not owner_email:
            continue

        candidate_name = call.job_application.candidate_name
        call_name = call.get_call_type_display()
        missing_list = ", ".join(missing_materials)
        completed_at = call.end_time.isoformat()
        subject = f"Reminder: {call_name} materials for {candidate_name} ({completed_at})"
        if EmailLog.objects.filter(
            recipient_email=owner_email,
            subject=subject,
            event="onboarding_call_material_reminder",
            candidate=call.job_application,
            status="sent",
        ).exists():
            continue

        send_email(
            to=owner_email,
            subject=subject,
            text=(
                f"Please upload {missing_list} for {candidate_name}'s "
                f"{call_name.lower()}."
            ),
            event="onboarding_call_material_reminder",
            email_type="internal",
            candidate=call.job_application,
            use_default_cc=False,
        )


def get_days_until_joining(application, now=None):
    """Return the real or simulated joining offset for an onboarding candidate."""
    now = now or timezone.now()

    if getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False):
        elapsed_minutes = max(
            int((now - application.created_at).total_seconds() // 60),
            0,
        )
        days_until_joining = DEBUG_ONBOARDING_MILESTONES[0][1]
        for milestone_minute, milestone_day in DEBUG_ONBOARDING_MILESTONES:
            if elapsed_minutes < milestone_minute:
                break
            days_until_joining = milestone_day
        logger.debug(
            "[DEBUG MODE] Candidate %s: elapsed_minutes=%s, "
            "mapped_days_until_joining=%s",
            application.candidate_name,
            elapsed_minutes,
            days_until_joining,
        )
        return days_until_joining

    joining_date = getattr(application, 'joining_date', None)
    return (joining_date - now.date()).days if joining_date else 999


def _send_manager_assignment_reminders(application):
    if not getattr(application, 'hod_email', None):
        logger.info(
            "HOD not assigned for %s. Sending hod_assignment_reminder.",
            application.candidate_name,
        )
        notify_internal(application, "hod_assignment_reminder")

    if not getattr(application, 'reporting_manager_email', None):
        logger.info(
            "Reporting Manager not assigned for %s. "
            "Sending reporting_manager_assignment_reminder.",
            application.candidate_name,
        )
        notify_internal(application, "reporting_manager_assignment_reminder")


def is_candidate_bgv_completed(application):
    """
    Check if a candidate's BGV is completed across CandidateBGV, JobApplication.bgv_status,
    JobApplication.status, and ApprovalNote.bgv_status.
    Returns (is_completed: bool, resolved_status: str).
    """
    app_bgv_status = getattr(application, 'bgv_status', None)
    if app_bgv_status and str(app_bgv_status).strip().lower() in BGV_COMPLETED_STATUSES:
        return True, str(app_bgv_status).strip().lower()

    app_status = getattr(application, 'status', None)
    if app_status and str(app_status).strip().lower() in BGV_COMPLETED_STATUSES:
        return True, str(app_status).strip().lower()

    bgv_status = None
    try:
        from bgv.models import CandidateBGV
        bgv = CandidateBGV.objects.filter(candidate=application).first()
        if bgv and bgv.status:
            bgv_status = str(bgv.status).strip().lower()
            if bgv_status in BGV_COMPLETED_STATUSES:
                return True, bgv_status
    except Exception:
        pass

    try:
        from onboarding.models import ApprovalNote
        note = ApprovalNote.objects.filter(candidate=application).order_by('-id').first()
        if note and note.bgv_status:
            nst = str(note.bgv_status).strip().lower()
            if nst in BGV_COMPLETED_STATUSES:
                return True, nst
    except Exception:
        pass

    resolved = bgv_status or (str(app_bgv_status).strip().lower() if app_bgv_status else "pending")
    return False, resolved


def process_daily_onboarding_policy_emails(app, days_until_joining):
    """
    Sends 1 post-welcome policy/handbook email every morning starting from Day 2:
      Day 2 (DOJ + 1): HR Handbook
      Day 3 (DOJ + 2): Culture & Values Handbook
      Day 4 (DOJ + 3): POSH Policy & Guidelines
      Day 5 (DOJ + 4): HR Buddy Chatbot User Manual
      Day 6 (DOJ + 5): KAI Happiness Mascot Check-in
    Ensures at most 1 email is sent per morning run.
    """
    if days_until_joining > -1:
        return None

    if getattr(app, 'is_post_welcome_docs_sent', False):
        return None

    work_email = (getattr(app, 'work_email', None) or '').strip()
    if not work_email and hasattr(app, 'refresh_from_db'):
        try:
            app.refresh_from_db(fields=['work_email'])
            work_email = (getattr(app, 'work_email', None) or '').strip()
        except Exception:
            pass

    is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
    if not work_email:
        if is_debug and getattr(app, 'candidate_email', None):
            work_email = app.candidate_email
            logger.info(f"[DEBUG SIMULATION] Using candidate_email {work_email} for daily policy emails for {app.candidate_name}.")
        else:
            logger.info(f"Work email missing for {app.candidate_name}. Deferring daily policy email.")
            return None

    from .notifications import (
        send_hr_handbook_email,
        send_culture_values_email,
        send_posh_policy_email,
        send_chatbot_manual_email,
        send_kai_mascot_email,
    )
    from onboarding.models import EmailLog

    def _already_sent(flag_attr, event_name):
        if getattr(app, flag_attr, False):
            return True
        return EmailLog.objects.filter(candidate=app, event=event_name, status='sent').exists()

    daily_policy_steps = [
        (1, 'is_hr_handbook_sent', 'hr_handbook', send_hr_handbook_email),
        (2, 'is_culture_values_sent', 'culture_values', send_culture_values_email),
        (3, 'is_posh_policy_sent', 'posh_policy', send_posh_policy_email),
        (4, 'is_chatbot_manual_sent', 'chatbot_manual', send_chatbot_manual_email),
        (5, 'is_kai_mascot_sent', 'kai_mascot', send_kai_mascot_email),
    ]

    days_past = abs(days_until_joining)

    for min_days, flag_attr, event_name, send_fn in daily_policy_steps:
        if not _already_sent(flag_attr, event_name):
            if days_past >= min_days:
                logger.info(
                    f"[ONBOARDING MORNING TASK] Candidate {app.candidate_name} (Day {days_past + 1}): "
                    f"Sending daily policy email '{event_name}'."
                )
                sent = send_fn(app)
                if sent:
                    setattr(app, flag_attr, True)
                    save_cols = [flag_attr]
                    if all(_already_sent(f, e) for _, f, e, _ in daily_policy_steps):
                        app.is_post_welcome_docs_sent = True
                        save_cols.append('is_post_welcome_docs_sent')
                    try:
                        app.save(update_fields=save_cols)
                    except Exception as err:
                        logger.warning(f"Could not update {flag_attr} for {app.candidate_name}: {err}")
                    return event_name
                return None
            else:
                # Milestone not reached yet
                break

    return None


def daily_onboarding_check():
    """
    Daily task to scan all candidates in 'offer_accepted', 'docs_pending', 'joining_pending' or 'joined' status,
    and trigger actions + auto-generate OnboardingTask records based on (joining_date - today).
    """
    logger.info("Running daily_onboarding_check...")
    # First, run joining date check: transition candidates with work_email on/after joining date to joined
    try:
        from onboarding.utils.joining_check import run_joining_date_check
        run_joining_date_check()
    except Exception as e:
        logger.error(f"Error executing run_joining_date_check in daily_onboarding_check: {e}")

    remind_call_owners_for_missing_materials()

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

    # me_client = ManageEngineClient()

    for app in candidates:
        days_until_joining = get_days_until_joining(app)

        # Gate: The onboarding task milestones will ONLY start after the onboarding initiation form is filled.
        # For candidates who have already joined, the initiation reminder email should NOT be sent.
        if not hasattr(app, 'onboarding_form'):
            if (getattr(app, 'status', None) or '').strip().lower() == "joined":
                logger.debug(f"Candidate {app.candidate_name} is already joined. Skipping onboarding initiation reminder.")
            else:
                logger.info(f"Onboarding form pending for candidate {app.candidate_name}. Sending reminder.")
                # Send reminder until it is filled
                notify_internal(app, "onboarding_initiation_reminder")
                continue

        if days_until_joining <= 0 and not getattr(app, 'is_joining_day_manager_email_sent', False):
            if getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False):
                logger.info(
                    "Skipping joining-day manager email for %s while onboarding debug mode is enabled.",
                    app.candidate_name,
                )
            else:
                from .joining_manager_email import send_joining_day_manager_email

                if send_joining_day_manager_email(app):
                    app.is_joining_day_manager_email_sent = True
                    app.save(update_fields=['is_joining_day_manager_email_sent'])

        # ── DOJ - 15 Days ───────────────────────────────────────
        if days_until_joining <= 15 and not getattr(app, 'is_doj_minus_15_triggered', False) and app.status != "joined":
            logger.info(f"DOJ - 15 for candidate {app.candidate_name}. Updating ME ticket.")
            # if app.it_ticket_ref:
            #     update_payload = {} # You can add specific custom fields here for procurement
            #     note = f"DOJ is in 15 days ({app.joining_date}). Please procure laptop."
            #     if app.job.job_type != 'work_from_office':
            #         note += " (Remote joiner: VPN setup task required)."
            #     me_client.update_ticket(app.it_ticket_ref, update_payload, note=note)

            # Send Email to IT Team
            notify_internal(app, "doj_minus_15_it_team")

            _send_manager_assignment_reminders(app)

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
            # else:
            #     if app.it_ticket_ref:
            #         note = f"DOJ is in 7 days ({app.joining_date}). Remote joiner. Please arrange for laptop dispatch."
            #         me_client.update_ticket(app.it_ticket_ref, {}, note=note)

            create_milestone_tasks(app, "DOJ_MINUS_7", app.joining_date)
            app.is_doj_minus_7_triggered = True
            app.save(update_fields=['is_doj_minus_7_triggered'])
            app.refresh_from_db(fields=['is_doj_minus_2_triggered'])

        # ── DOJ - 2 Days ────────────────────────────────────────
        if days_until_joining <= 2 and not app.is_doj_minus_2_triggered and app.status != "joined":
            logger.info(f"DOJ - 2 for candidate {app.candidate_name}. Welcome Email.")
            location = "Gurugram"
            try:
                from onboarding.models import ApprovalNote
                an = ApprovalNote.objects.filter(candidate=app, status='approved').last()
                if hasattr(app, 'onboarding_form') and app.onboarding_form.center_office_location:
                    location = app.onboarding_form.center_office_location
                elif an and an.payload.get('mrf', {}).get('location'):
                    location = an.payload['mrf']['location']
                elif app.job and hasattr(app.job, 'mrf') and app.job.mrf.location:
                    location = app.job.mrf.location
            except Exception as e:
                logger.error(f"Failed to fetch location for welcome email: {e}")
            job_type = getattr(app.job, 'job_type', 'work_from_office') if app.job else 'work_from_office'
            send_welcome_email(app, work_type=job_type, reporting_time="10:30 AM", office_address=location, hr_contact_details="Team HR (hr@knowcraft.in)", cc=[])

            # if app.it_ticket_ref and getattr(app.job, 'job_type', None) != 'work_from_office':
            #     me_client.update_ticket(app.it_ticket_ref, {}, note="DOJ is in 2 days. Finalize VPN/dispatch tasks.")
            
            app.is_doj_minus_2_triggered = True
            app.save(update_fields=['is_doj_minus_2_triggered'])

        # ── DOJ 0 — Statutory docs + Handbooks & Policies + Zoho Sign packet ────────────
        if days_until_joining <= 0 and not getattr(app, 'is_doj_0_triggered', False):
            work_email = (getattr(app, 'work_email', None) or '').strip()
            if not work_email and hasattr(app, 'refresh_from_db'):
                try:
                    app.refresh_from_db(fields=['work_email'])
                    work_email = (getattr(app, 'work_email', None) or '').strip()
                except Exception:
                    pass

            if not work_email:
                logger.info(f"Work email missing for {app.candidate_name}. Skipping post-joining tasks.")
                if hasattr(app, 'onboarding_form'):
                    notify_internal(app, "missing_work_email_reminder")
                continue

            app.work_email = work_email
            is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
            
            # Note: Handbooks & policies are sent 1 per day starting from Day 2 morning check
            # via process_daily_onboarding_policy_emails()

            if (app.status == "joined" or is_debug) and not getattr(app, 'is_esign_packet_generated', False):
                logger.info(f"DOJ 0 for candidate {app.candidate_name}. Generating esign doc records.")
                generate_esign_documents(app)
                # app.is_esign_packet_generated = True
                # app.save(update_fields=['is_esign_packet_generated'])

            # Always attempt sending — catches docs HR uploaded after DOJ 0 fired.
            # In debug mode we skip the real Zoho API call.
            if getattr(app, 'is_esign_packet_generated', False) and not is_debug:
                send_documents_for_esign(app)

            app.is_doj_0_triggered = True
            app.save(update_fields=['is_doj_0_triggered'])

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

        # ── Day 2+ (DOJ + 1 onwards) — Daily Policy & Handbook emails (1 per morning) ──
        if days_until_joining <= -1:
            try:
                process_daily_onboarding_policy_emails(app, days_until_joining)
            except Exception as err:
                logger.error(f"Error in process_daily_onboarding_policy_emails for {app.candidate_name}: {err}", exc_info=True)

        # ── DOJ + 5 Days (Document Verification & Undertaking Sign-off) ────────
        if days_until_joining <= -5:
            # Document verification must ONLY be sent after all e-sign docs are uploaded
            if not getattr(app, 'is_d5_verification_sent', False):
                esign_docs = app.esign_documents.all()
                esign_docs_uploaded = esign_docs.exists() and not esign_docs.filter(source_file="").exists()
                is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)

                if not esign_docs_uploaded and not is_debug:
                    logger.info(f"DOJ + 5 for candidate {app.candidate_name}: e-sign docs not yet uploaded. Deferring document verification email.")
                else:
                    logger.info(f"DOJ + 5 for candidate {app.candidate_name}. Sending document verification email.")
                    if notify_candidate(app, "d5_document_verification", cc=[]):
                        app.is_d5_verification_sent = True
                        app.save(update_fields=['is_d5_verification_sent'])

            # Send Undertaking Sign-off Document via Zoho Sign template
            if not getattr(app, 'is_undertaking_signoff_sent', False):
                logger.info(f"DOJ + 5 for candidate {app.candidate_name}. Sending Undertaking Sign-off Document.")
                try:
                    from .zoho_sign import send_undertaking_signoff
                    result = send_undertaking_signoff(app)
                    if result:
                        app.is_undertaking_signoff_sent = True
                        app.save(update_fields=['is_undertaking_signoff_sent'])
                except Exception as e:
                    logger.error(f"Failed to send undertaking sign-off for {app.candidate_name}: {e}")

        # ── DOJ + 7 Days (Escalation Check) ─────────────────────
        if days_until_joining <= -7 and not getattr(app, 'is_doj_7_triggered', False):
            logger.info(f"DOJ + 7 for candidate {app.candidate_name}. Checking BGV status.")

            # Set triggered flag and milestone task FIRST to prevent duplicate executions
            create_milestone_tasks(app, "DOJ_PLUS_7_BGV", app.joining_date)
            app.is_doj_7_triggered = True
            app.save(update_fields=['is_doj_7_triggered'])

            designation_name = app.job.mrf.designation.name.lower() if (
                hasattr(app, 'job') and app.job and
                hasattr(app.job, 'mrf') and app.job.mrf and
                app.job.mrf.designation
            ) else ""
            is_intern = 'intern' in designation_name
            is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)

            if not is_debug and not is_intern:
                bgv_done, resolved_status = is_candidate_bgv_completed(app)
                if bgv_done:
                    logger.info(
                        f"DOJ + 7: BGV for {app.candidate_name} is '{resolved_status}' — no escalation needed."
                    )
                    if getattr(app, 'is_escalated', False):
                        app.is_escalated = False
                        app.save(update_fields=['is_escalated'])
                else:
                    if not getattr(app, 'is_escalated', False):
                        app.is_escalated = True
                        app.save(update_fields=['is_escalated'])
                        logger.warning(
                            f"DOJ + 7: BGV for {app.candidate_name} is '{resolved_status}' — escalating."
                        )
                        notify_internal(app, "bgv_escalation", cc=['zafiya.mallick@knowcraft.in'])

        days_past = 0
        if days_until_joining < 0:
            days_past = abs(days_until_joining)

        # If candidate was previously escalated but BGV is now completed, clear escalation flag
        if getattr(app, 'is_escalated', False) and is_candidate_bgv_completed(app)[0]:
            logger.info(f"Candidate {app.candidate_name} BGV is now completed. Clearing is_escalated flag.")
            app.is_escalated = False
            app.save(update_fields=['is_escalated'])

        # ── DOJ + 30 Days ─────────────────────────────────────────
        if days_past >= 30 and not getattr(app, 'is_d30_survey_sent', False):
            logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Sending 30-day candidate survey reminder.")
            if notify_candidate(app, "satisfaction_survey", cc=[]):
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
            success_candidate = notify_candidate(app, "d90_survey", cc=[])
            if success_candidate:
                app.is_d90_survey_sent = True
                app.save(update_fields=['is_d90_survey_sent'])
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

        if days_past >= 90 and app.is_d90_survey_filled and app.is_d90_call_scheduled and not getattr(app, 'it_ticket_closed', False):
            logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Requesting IT team to close ticket.")
            notify_internal(app, "it_ticket_close_request")
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
    faked_created_at = getattr(app, 'created_at', None)
    try:
        app.refresh_from_db()
    except Exception as e:
        logger.warning(f"Could not refresh candidate {getattr(app, 'pk', None)} from DB: {e}")
    finally:
        if faked_created_at:
            app.created_at = faked_created_at

    logger.info(f"[ADMIN ACTION] Running onboarding check for: {app.candidate_name}")

    # me_client = ManageEngineClient()
    joining_date = app.joining_date
    if not joining_date:
        logger.error(f"[ADMIN ACTION] Candidate {app.candidate_name} has no joining date.")
        return 999
        
    days_until_joining = get_days_until_joining(app)
    logger.debug(
        "[ADMIN ACTION] %s: days_until_joining=%s",
        app.candidate_name,
        days_until_joining,
    )

    # ── DOJ - 15 Days ───────────────────────────────────────────────────────
    if days_until_joining <= 15 and not getattr(app, 'is_doj_minus_15_triggered', False) and app.status != "joined":
        logger.info(f"[ADMIN ACTION] DOJ - 15 for {app.candidate_name}. Updating ME ticket.")
        # if app.it_ticket_ref:
        #     note = f"DOJ is in 15 days ({joining_date}). Please procure laptop."
        #     if app.job and app.job.job_type != 'work_from_office':
        #         note += " (Remote joiner: VPN setup task required)."
        #     me_client.update_ticket(app.it_ticket_ref, {}, note=note)
        notify_internal(app, "doj_minus_15_it_team")
        _send_manager_assignment_reminders(app)
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
            if hasattr(app, 'onboarding_form') and app.onboarding_form.center_office_location:
                location = app.onboarding_form.center_office_location
            elif an and an.payload.get('mrf', {}).get('location'):
                location = an.payload['mrf']['location']
            elif app.job and hasattr(app.job, 'mrf') and app.job.mrf.location:
                location = app.job.mrf.location
        except Exception as e:
            logger.error(f"Failed to fetch location for welcome email: {e}")

        job_type = getattr(app.job, 'job_type', 'work_from_office') if app.job else 'work_from_office'
        send_welcome_email(app, work_type=job_type, reporting_time="10:30 AM", office_address=location, hr_contact_details="Team HR (hr@knowcraft.in)", cc=[])
        # if app.it_ticket_ref and app.job and app.job.job_type != 'work_from_office':
            # me_client.update_ticket(app.it_ticket_ref, {}, note="DOJ is in 2 days. Finalize VPN/dispatch tasks.")
            
        app.is_doj_minus_2_triggered = True
        app.save(update_fields=['is_doj_minus_2_triggered'])

    # ── DOJ 0 — Statutory docs + Handbooks & Policies + e-sign packet ─────────────────────────────
    if days_until_joining <= 0 and not getattr(app, 'is_doj_0_triggered', False):
        work_email = (getattr(app, 'work_email', None) or '').strip()
        if not work_email and hasattr(app, 'refresh_from_db'):
            try:
                app.refresh_from_db(fields=['work_email'])
                work_email = (getattr(app, 'work_email', None) or '').strip()
            except Exception:
                pass

        if not work_email:
            logger.info(f"[ADMIN ACTION] Work email missing for {app.candidate_name}. Skipping post-joining tasks.")
            if hasattr(app, 'onboarding_form'):
                notify_internal(app, "missing_work_email_reminder")
            return days_until_joining

        app.work_email = work_email
        is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)
        
        # Note: Handbooks & policies are sent 1 per day starting from Day 2 morning check
        # via process_daily_onboarding_policy_emails()

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

    # ── Day 2+ (DOJ + 1 onwards) — Daily Policy & Handbook emails (1 per morning) ──
    if days_until_joining <= -1:
        try:
            process_daily_onboarding_policy_emails(app, days_until_joining)
        except Exception as err:
            logger.error(f"[ADMIN ACTION] Error in process_daily_onboarding_policy_emails for {app.candidate_name}: {err}", exc_info=True)

    # ── DOJ + 5 Days — Document Verification & Undertaking Sign-off ─────────
    if days_until_joining <= -5:
        # Document verification must ONLY be sent after all e-sign docs are uploaded
        if not getattr(app, 'is_d5_verification_sent', False):
            esign_docs = app.esign_documents.all()
            esign_docs_uploaded = esign_docs.exists() and not esign_docs.filter(source_file="").exists()
            is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)

            if not esign_docs_uploaded and not is_debug:
                logger.info(f"[ADMIN ACTION] DOJ + 5 for {app.candidate_name}: e-sign docs not yet uploaded. Deferring document verification email.")
            else:
                logger.info(f"[ADMIN ACTION] DOJ + 5 for {app.candidate_name}. Sending document verification email.")
                if notify_candidate(app, "d5_document_verification", cc=[]):
                    app.is_d5_verification_sent = True
                    app.save(update_fields=['is_d5_verification_sent'])

        # Send Undertaking Sign-off Document via Zoho Sign template
        if not getattr(app, 'is_undertaking_signoff_sent', False):
            logger.info(f"[ADMIN ACTION] DOJ + 5 for {app.candidate_name}. Sending Undertaking Sign-off Document.")
            try:
                from .zoho_sign import send_undertaking_signoff
                result = send_undertaking_signoff(app)
                if result:
                    app.is_undertaking_signoff_sent = True
                    app.save(update_fields=['is_undertaking_signoff_sent'])
            except Exception as e:
                logger.error(f"[ADMIN ACTION] Failed to send undertaking sign-off for {app.candidate_name}: {e}")

    # ── DOJ + 7 Days — BGV check ────────────────────────────────────────────
    if days_until_joining <= -7 and not getattr(app, 'is_doj_7_triggered', False):
        logger.info(f"[ADMIN ACTION] DOJ + 7 for {app.candidate_name}. Checking BGV status.")
        create_milestone_tasks(app, "DOJ_PLUS_7_BGV", joining_date)
        app.is_doj_7_triggered = True
        app.save(update_fields=['is_doj_7_triggered'])

        designation_name = app.job.mrf.designation.name.lower() if (
            app.job and app.job.mrf and app.job.mrf.designation
        ) else ""
        is_intern = 'intern' in designation_name
        is_debug = getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False)

        if not is_debug and not is_intern:
            bgv_done, resolved_status = is_candidate_bgv_completed(app)
            if bgv_done:
                logger.info(
                    f"[ADMIN ACTION] DOJ + 7: BGV for {app.candidate_name} is '{resolved_status}' — "
                    f"no escalation needed."
                )
                if getattr(app, 'is_escalated', False):
                    app.is_escalated = False
                    app.save(update_fields=['is_escalated'])
            else:
                if not getattr(app, 'is_escalated', False):
                    app.is_escalated = True
                    app.save(update_fields=['is_escalated'])
                    logger.warning(
                        f"[ADMIN ACTION] DOJ + 7: BGV for {app.candidate_name} is '{resolved_status}' — "
                        f"escalating."
                    )
                    notify_internal(app, "bgv_escalation", cc=['zafiya.mallick@knowcraft.in'])

    days_past = abs(days_until_joining) if days_until_joining < 0 else 0

    # If candidate was previously escalated but BGV is now completed, clear escalation flag
    if getattr(app, 'is_escalated', False) and is_candidate_bgv_completed(app)[0]:
        logger.info(f"[ADMIN ACTION] Candidate {app.candidate_name} BGV is now completed. Clearing is_escalated flag.")
        app.is_escalated = False
        app.save(update_fields=['is_escalated'])

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

    if days_past >= 90 and app.is_d90_survey_filled and app.is_d90_call_scheduled and not getattr(app, 'it_ticket_closed', False):
        logger.info(f"[ADMIN ACTION] DOJ + {days_past} for {app.candidate_name}. Requesting IT team to close ticket.")
        notify_internal(app, "it_ticket_close_request")
        app.it_ticket_closed = True
        app.save(update_fields=['it_ticket_closed'])

    logger.info(f"[ADMIN ACTION] Completed onboarding check for: {app.candidate_name}")
    return days_until_joining
