# onboarding/utils/onboarding_tasks.py

import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from jobs.models import JobApplication
from bgv.models import CandidateBGV
from .zoho_manageengine import ManageEngineClient
from .notifications import notify_candidate, notify_internal
# Assuming we will add HTML email templates in onboarding/utils/templates.py
# or we use an existing email sender.

logger = logging.getLogger(__name__)

def daily_onboarding_check():
    """
    Daily task to scan all candidates in 'offer_accepted', 'docs_pending', 'joining_pending' or 'joined' status,
    and trigger actions based on (joining_date - today).
    """
    logger.info("Running daily_onboarding_check...")
    
    today = timezone.now().date()
    
    # We only care about active applications that have a joining date and have accepted the offer.
    # Exclude candidates who have completed onboarding or are rejected/withdrawn.
    active_statuses = [
        "offer_accepted", "docs_pending", "docs_uploaded", 
        "joining_pending", "joined"
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

        # ── DOJ - 7 Days ────────────────────────────────────────
        elif days_until_joining == 7:
            logger.info(f"DOJ - 7 for candidate {app.candidate_name}.")
            if app.job.job_type == 'work_from_office':
                # Office Joiner
                notify_internal(app, "doj_minus_7_hod")
                notify_internal(app, "doj_minus_7_admin")
            else:
                # Remote Joiner
                if app.it_ticket_ref:
                    note = f"DOJ is in 7 days ({app.joining_date}). Remote joiner. Please arrange for laptop dispatch."
                    me_client.update_ticket(app.it_ticket_ref, {}, note=note)

        # ── DOJ - 2 Days ────────────────────────────────────────
        elif days_until_joining == 2:
            logger.info(f"DOJ - 2 for candidate {app.candidate_name}. Welcome Email.")
            # Send welcome email
            notify_candidate(app, "welcome_joining", cc=[])
            
            # Update ME Ticket
            if app.it_ticket_ref and app.job.job_type != 'work_from_office':
                me_client.update_ticket(app.it_ticket_ref, {}, note="DOJ is in 2 days. Finalize VPN/dispatch tasks.")

        # ── DOJ + 1 Day ─────────────────────────────────────────
        elif days_until_joining == -1:
            logger.info(f"DOJ + 1 for candidate {app.candidate_name}. FinOps / Docs Check.")
            if app.status == "docs_pending":
                notify_candidate(app, "login_request_reminder", cc=[])
                
            # FinOps API Stub
            # POST /documents/generate/
            logger.info("Triggering FinOps account creation API (stub)...")

        # ── DOJ + 7 Days (Escalation Check) ─────────────────────
        elif days_until_joining == -7:
            logger.info(f"DOJ + 7 for candidate {app.candidate_name}. Checking BGV status.")
            # Read BGV Status
            try:
                bgv = CandidateBGV.objects.get(candidate=app)
                if bgv.status not in ['clear', 'verified']:
                    # Escalate!
                    app.is_escalated = True
                    app.save(update_fields=['is_escalated'])
                    notify_internal(app, "bgv_escalation")
            except CandidateBGV.DoesNotExist:
                # No BGV record found, might also warrant an escalation
                app.is_escalated = True
                app.save(update_fields=['is_escalated'])
                notify_internal(app, "bgv_escalation")

        # ── DOJ + 30 Days (Satisfaction Survey) ─────────────────
        elif days_until_joining <= -30:
            days_past = abs(days_until_joining)
            
            # Send candidate survey reminder if not filled
            if not app.is_satisfaction_survey_filled:
                if days_past >= 30:
                    logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Sending candidate survey reminder.")
                    notify_candidate(app, "satisfaction_survey", cc=[])
            
            # Send HOD survey reminder if not filled
            if not app.is_hod_survey_filled:
                if days_past >= 30:
                    logger.info(f"DOJ + {days_past} for candidate {app.candidate_name}. Sending HOD survey reminder.")
                    notify_internal(app, "satisfaction_survey_hod")

        # ── DOJ + 45 Days (Check-in Call) ───────────────────────
        elif days_until_joining <= -45 and not app.is_d45_call_scheduled:
            logger.info(f"DOJ + {abs(days_until_joining)} for candidate {app.candidate_name}. Check-in invite reminder.")
            notify_internal(app, "schedule_checkin_call_reminder")
                
        # ── DOJ + 90 Days (Final Event & Close) ─────────────────
        elif days_until_joining <= -90 and not app.is_d90_call_scheduled:
            logger.info(f"DOJ + {abs(days_until_joining)} for candidate {app.candidate_name}. Final review reminder.")
            notify_internal(app, "schedule_final_review_reminder")
                
            # If it's exactly day 90, close the ME ticket
            if days_until_joining == -90:
                if app.it_ticket_ref:
                    me_client.close_ticket(app.it_ticket_ref)
                
    return True
