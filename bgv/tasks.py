# bgv/tasks.py

"""
Periodic background task that checks for experienced candidates
whose BGV scheduled date has arrived (15 days before joining),
and initiates their BGV process via OnGrid.
"""

import logging
import threading
from datetime import date

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# OnGrid → Internal status mapping
# ─────────────────────────────────────────────────────────────

ONGRID_STATUS_MAPPING = {
    # Active states
    "Initiated": "initiated",
    "Pending": "pending",
    "InProgress": "in_progress",
    "UnderReview": "under_review",
    "InsufficiencyRaised": "insufficiency_raised",
    "DataInsufficient": "data_insufficient",
    "AwaitingCandidateInput": "awaiting_candidate_input",
    "AwaitingEmployerResponse": "awaiting_employer_response",
    "AwaitingUniversityResponse": "awaiting_university_response",
    "AwaitingCourtResponse": "awaiting_court_response",

    # Successful / terminal states
    "Clear": "clear",
    "Completed": "completed",
    "Closed": "closed",
    "Verified": "verified",
    "UnableToVerify": "unable_to_verify",
    "Discrepancy": "discrepancy",

    # Failure states
    "Failed": "failed",
    "Cancelled": "cancelled",
    "Rejected": "rejected",
    "Expired": "expired",
}


def map_ongrid_status(status):
    """
    Convert OnGrid status to internal Django status.
    """
    if not status:
        return "in_progress"

    return ONGRID_STATUS_MAPPING.get(
        str(status).strip(),
        "in_progress",
    )


def run_bgv_schedule_check():
    """
    Find all CandidateBGV records with status='pending_schedule'
    whose bgv_scheduled_date <= today, and initiate BGV for them.
    """
    from .models import CandidateBGV
    from .services import send_notification_for_bgv

    print("[BGV SCHEDULER] Starting check for scheduled BGV triggers...")

    try:
        pending_bgvs = list(
            CandidateBGV.objects.filter(
                status="pending_schedule",
                bgv_scheduled_date__lte=date.today(),
                bgv_scheduled_date__isnull=False,
            ).select_related("candidate")
        )

        if not pending_bgvs:
            print("[BGV SCHEDULER] No scheduled BGV records found to process.")
            return

        for bgv_record in pending_bgvs:
            candidate = bgv_record.candidate
            print(
                f"[BGV SCHEDULER] Sending BGV initiation link to experienced candidate "
                f"{candidate.candidate_name} (app={candidate.id}, "
                f"scheduled={bgv_record.bgv_scheduled_date})"
            )
            try:
                send_notification_for_bgv(candidate)
                logger.info(
                    "BGV initiation link sent to scheduled candidate %s (app=%s)",
                    candidate.candidate_name, candidate.id,
                )
            except Exception as exc:
                logger.exception(
                    "Failed to send BGV initiation link to candidate %s (app=%s): %s",
                    candidate.candidate_name, candidate.id, exc,
                )

        print(
            f"[BGV SCHEDULER] Processed {len(pending_bgvs)} scheduled BGV records."
        )

    except Exception as exc:
        logger.error("[BGV SCHEDULER] Error during scheduled BGV check: %s", exc)


def run_bgv_status_poll():
    """
    Poll latest BGV status from OnGrid and sync with CandidateBGV.
    """
    from django.utils import timezone
    from .models import CandidateBGV
    from .services import (
        get_verification_report,
        get_individual_status,
    )

    print("[BGV POLLER] Starting check for active BGV records...")

    try:
        active_bgvs = list(
            CandidateBGV.objects.exclude(
                status__in=[
                    "completed",
                    "clear",
                    "verified",
                    "closed",
                    "failed",
                    "cancelled",
                    "rejected",
                    "expired",
                ]
            )
            .exclude(ongrid_individual_id="")
            .exclude(ongrid_individual_id__isnull=True)
            .select_related("candidate")
        )

        if not active_bgvs:
            print("[BGV POLLER] No active BGV records to poll.")
            return

        for bgv_record in active_bgvs:

            print(
                f"[BGV POLLER] Polling status for "
                f"{bgv_record.candidate.candidate_name} "
                f"({bgv_record.ongrid_individual_id})"
            )

            report = get_verification_report(
                bgv_record.ongrid_individual_id
            )

            if not report:
                logger.warning(
                    "No report received for individual %s",
                    bgv_record.ongrid_individual_id,
                )
                continue

            old_status = bgv_record.status
            update_fields = []

            # Save latest payload
            bgv_record.callback_payload = report
            update_fields.append("callback_payload")

            # -------------------------------------------------
            # Extract overall status
            # -------------------------------------------------

            overall_status = (
                report.get("status")
                or report.get("overallStatus")
                or report.get("verificationStatus")
            )

            # Fallback from verification list
            if not overall_status:

                verifications = report.get("verifications", [])

                if verifications:

                    statuses = [
                        v.get("status")
                        for v in verifications
                        if v.get("status")
                    ]

                    if statuses:
                        overall_status = statuses[0]

            # Map to internal status
            new_status = map_ongrid_status(overall_status)

            print(
                f"[BGV POLLER] OnGrid status={overall_status} "
                f"mapped={new_status}"
            )

            # -------------------------------------------------
            # Update status only if changed
            # -------------------------------------------------

            if new_status != old_status:
                bgv_record.status = new_status
                update_fields.append("status")

                # Terminal statuses
                if new_status in [
                    "completed",
                    "clear",
                    "verified",
                    "closed",
                ]:
                    bgv_record.completed_at = timezone.now()
                    update_fields.append("completed_at")

                # Fetch report URL
                try:

                    individual_data = get_individual_status(
                        bgv_record.ongrid_individual_id
                    )

                    if individual_data:

                        report_url = (
                            individual_data.get("reportUrl")
                            or individual_data.get("report_url")
                        )

                        if report_url:
                            bgv_record.report_url = report_url
                            update_fields.append("report_url")
                except Exception:
                    logger.warning(
                        "Failed to fetch report URL "
                        "(individual=%s)",
                        bgv_record.ongrid_individual_id,
                    )

                # Full save to trigger signals
                bgv_record.save()

                logger.info(
                    "BGV status updated for %s: %s → %s",
                    bgv_record.candidate.candidate_name,
                    old_status,
                    new_status,
                )

            else:
                # Save only payload changes
                bgv_record.save(update_fields=update_fields)

        print(
            f"[BGV POLLER] Polled {len(active_bgvs)} BGV records."
        )

    except Exception as exc:
        logger.exception(
            "[BGV POLLER] Error during BGV poll: %s",
            exc,
        )


def run_bgv_schedule_check_and_reschedule():
    """
    Run scheduler + poller and reschedule after 1 hour.
    """

    from onboarding.utils.task_queue import TASK_QUEUE

    run_bgv_schedule_check()
    run_bgv_status_poll()

    timer = threading.Timer(
        3600,
        lambda: TASK_QUEUE.enqueue(
            run_bgv_schedule_check_and_reschedule
        ),
    )

    timer.daemon = True
    timer.start()


def schedule_periodic_bgv_check():
    """
    Initial entry point.
    """

    from onboarding.utils.task_queue import TASK_QUEUE

    TASK_QUEUE.enqueue(
        run_bgv_schedule_check_and_reschedule
    )

    print(
        "[BGV SCHEDULER] "
        "Periodic BGV schedule & poll check registered."
    )