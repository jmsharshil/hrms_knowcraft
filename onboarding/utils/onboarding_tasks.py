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
        is_escalated=False # Skip candidates actively in escalation
    )

    me_client = ManageEngineClient()

    for app in candidates:
        if getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False):
            # Test Mode: Use minutes since creation to simulate the timeline.
            # Assuming 'Joining' occurs exactly 15 minutes after creation.
            # Thus:
            # minute 0 = DOJ - 15
            # minute 8 = DOJ - 7
            # minute 13 = DOJ - 2
            # minute 15 = DOJ (0)
            # minute 22 = DOJ + 7
            # minute 45 = DOJ + 30
            # minute 60 = DOJ + 45
            # minute 105 = DOJ + 90
            minutes_since_creation = int((timezone.now() - app.created_at).total_seconds() / 60)
            days_until_joining = 15 - minutes_since_creation
            logger.debug(f"[DEBUG MODE] Candidate {app.candidate_name}: minutes_since_creation={minutes_since_creation}, mapped_days_until_joining={days_until_joining}")
        else:
            days_until_joining = (app.joining_date - today).days

        # ── DOJ - 15 Days ───────────────────────────────────────
        if days_until_joining == 15:
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

        # ── DOJ - 7 Days ────────────────────────────────────────
        elif days_until_joining == 7:
            logger.info(f"DOJ - 7 for candidate {app.candidate_name}.")
            if app.job.job_type == 'work_from_office':
                notify_internal(app, "doj_minus_7_hod")
                notify_internal(app, "doj_minus_7_admin")
            else:
                if app.it_ticket_ref:
                    note = f"DOJ is in 7 days ({app.joining_date}). Remote joiner. Please arrange for laptop dispatch."
                    me_client.update_ticket(app.it_ticket_ref, {}, note=note)

            create_milestone_tasks(app, "DOJ_MINUS_7", app.joining_date)

        # ── DOJ - 2 Days ────────────────────────────────────────
        elif days_until_joining == 2:
            logger.info(f"DOJ - 2 for candidate {app.candidate_name}. Welcome Email.")
            notify_candidate(app, "welcome_joining", cc=[])

            if app.it_ticket_ref and app.job.job_type != 'work_from_office':
                me_client.update_ticket(app.it_ticket_ref, {}, note="DOJ is in 2 days. Finalize VPN/dispatch tasks.")

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
        elif days_until_joining == 0:
            if app.status == "joined" and not getattr(app, 'is_esign_packet_generated', False):
                logger.info(f"DOJ 0 for candidate {app.candidate_name}. Generating esign doc records.")
                generate_esign_documents(app)
                app.is_esign_packet_generated = True
                app.save(update_fields=['is_esign_packet_generated'])
                create_milestone_tasks(app, "DOJ_0_DOCS", app.joining_date)

            # Always attempt sending — catches docs HR uploaded after DOJ 0 fired
            if getattr(app, 'is_esign_packet_generated', False):
                send_documents_for_esign(app)

        # ── DOJ + 1 Day — esign reminder (real implementation, was a stub) ─────
        elif days_until_joining == -1:
            if getattr(app, 'is_esign_packet_generated', False) and not getattr(app, 'is_esign_reminder_sent', False):
                logger.info(f"DOJ + 1 for candidate {app.candidate_name}. Checking for unsigned esign docs.")
                send_esign_reminders(app)
                app.is_esign_reminder_sent = True
                app.save(update_fields=['is_esign_reminder_sent'])
                create_milestone_tasks(app, "DOJ_PLUS_1_ESIGN_REMINDER", app.joining_date)

        # ── DOJ + 7 Days (Escalation Check) ─────────────────────
        elif days_until_joining == -7:
            logger.info(f"DOJ + 7 for candidate {app.candidate_name}. Checking BGV status.")
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
            create_milestone_tasks(app, "DOJ_PLUS_30_SURVEY", app.joining_date)

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

        # ── DOJ + 45 Days ───────────────────────
        if days_past >= 45 and not getattr(app, 'is_d45_call_scheduled', False):
            logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Check-in invite reminder (D45).")
            notify_internal(app, "schedule_checkin_call_reminder")
            create_milestone_tasks(app, "DOJ_PLUS_45_CHECKIN", app.joining_date)

        # ── DOJ + 90 Days ─────────────
        if days_past >= 90 and not getattr(app, 'is_d90_survey_sent', False):
            logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Sending 90-day survey + final review reminder.")
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
                logger.warning(f"Could not create 90-day SurveyResponse record for {app.candidate_name}: {survey_err}")

            app.is_d90_survey_sent = True
            app.save(update_fields=['is_d90_survey_sent'])
            create_milestone_tasks(app, "DOJ_PLUS_90_FINAL", app.joining_date)

        if days_past >= 90 and app.it_ticket_ref and not getattr(app, 'it_ticket_closed', False):
            logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Closing ManageEngine IT ticket.")
            if me_client.close_ticket(app.it_ticket_ref):
                app.it_ticket_closed = True
                app.save(update_fields=['it_ticket_closed'])

    return True
