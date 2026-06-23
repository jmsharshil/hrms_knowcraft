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

def bgv_form_reminder_task(bgv_id):
    """
    Handler executed by TaskScheduler every 4 hours.
    Checks if the BGV status is still 'pending_data' (meaning the candidate 
    hasn't submitted the form). If so, it sends a reminder.
    Otherwise, it cancels the recurring task.
    """
    from .models import CandidateBGV
    from .services import send_notification_for_bgv
    from scheduler.services import TaskScheduler
    
    try:
        bgv = CandidateBGV.objects.get(id=bgv_id)
        if bgv.status == "pending_data":
            # Send the reminder
            send_notification_for_bgv(bgv.candidate, is_reminder=True)
            logger.info("BGV form reminder sent for candidate %s", bgv.candidate.candidate_name)
        else:
            # Form is filled, verifications initiated (or another terminal state)
            # Cancel the recurring reminder task
            TaskScheduler.cancel(
                task_type="bgv_form_reminder",
                task_kwargs_filter={"bgv_id": str(bgv_id)}
            )
            logger.info("BGV form reminder cancelled for candidate %s (status=%s)", bgv.candidate.candidate_name, bgv.status)
    except CandidateBGV.DoesNotExist:
        # Cancel if record is deleted
        TaskScheduler.cancel(
            task_type="bgv_form_reminder",
            task_kwargs_filter={"bgv_id": str(bgv_id)}
        )
        logger.warning("BGV record %s not found. Reminder task cancelled.", bgv_id)


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

    print("[BGV POLLER] ====== Starting BGV status poll ======")
    print(f"[BGV POLLER] Current time: {timezone.now()}")

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

        print(f"[BGV POLLER] Found {len(active_bgvs)} active BGV records to poll.")

        if not active_bgvs:
            print("[BGV POLLER] No active BGV records to poll. Exiting.")
            return

        for i, bgv_record in enumerate(active_bgvs, 1):
            candidate_name = bgv_record.candidate.candidate_name
            individual_id = bgv_record.ongrid_individual_id

            print(
                f"\n[BGV POLLER] --- [{i}/{len(active_bgvs)}] "
                f"Candidate: {candidate_name}, "
                f"IndividualID: {individual_id}, "
                f"Current Status: {bgv_record.status} ---"
            )

            # Step 1: Fetch verification report
            print(f"[BGV POLLER] Fetching verification report for {individual_id}...")
            report = get_verification_report(individual_id)

            old_status = bgv_record.status
            update_fields = []
            overall_status = None

            if not report:
                print(f"[BGV POLLER] ❌ No report received for {individual_id}.")
                logger.warning(
                    "No report received for individual %s",
                    individual_id,
                )
            else:
                print(f"[BGV POLLER] ✅ Report received. Keys: {list(report.keys())}")

                # Save latest payload
                bgv_record.callback_payload = report
                update_fields.append("callback_payload")

                # Check if report has a servingUrl
                report_url = report.get("servingUrl") or report.get("reportUrl") or report.get("consolidatedReportUrl")
                if report_url and bgv_record.report_url != report_url:
                    bgv_record.report_url = report_url
                    if "report_url" not in update_fields:
                        update_fields.append("report_url")

                # -------------------------------------------------
                # Extract overall status
                # -------------------------------------------------
                overall_status = (
                    report.get("status")
                    or report.get("overallStatus")
                    or report.get("verificationStatus")
                )

                print(
                    f"[BGV POLLER] Raw status fields — "
                    f"status={report.get('status')}, "
                    f"overallStatus={report.get('overallStatus')}, "
                    f"verificationStatus={report.get('verificationStatus')}"
                )

                # Fallback from verification list
                if not overall_status:
                    verifications = report.get("verifications", [])
                    print(f"[BGV POLLER] No direct status. Checking verifications list ({len(verifications)} items)...")

                    if verifications:
                        statuses = [
                            v.get("status")
                            for v in verifications
                            if v.get("status")
                        ]
                        print(f"[BGV POLLER] Verification statuses found: {statuses}")

                        if statuses:
                            overall_status = statuses[0]

            # -------------------------------------------------
            # Step 2: Fetch verification status (per-check statuses + report URL)
            # -------------------------------------------------
            print(f"[BGV POLLER] Fetching individual verification status for {individual_id}...")
            try:
                individual_data = get_individual_status(
                    individual_id,
                    bgv_instance=bgv_record,  # This triggers _persist_ongrid_status
                )
                if individual_data:
                    print(f"[BGV POLLER] ✅ Individual status received. Keys: {list(individual_data.keys())}")

                    report_url = (
                        individual_data.get("consolidatedReportUrl")
                        or individual_data.get("reportUrl")
                        or individual_data.get("report_url")
                    )
                    if report_url:
                        print(f"[BGV POLLER] 📄 Report URL found: {report_url}")
                        bgv_record.report_url = report_url
                        if "report_url" not in update_fields:
                            update_fields.append("report_url")
                    else:
                        print("[BGV POLLER] No report URL in individual status response.")
                else:
                    print(f"[BGV POLLER] ❌ No individual status data received for {individual_id}.")
            except Exception as exc:
                print(f"[BGV POLLER] ⚠️ Failed to fetch individual status: {exc}")
                logger.warning(
                    "Failed to fetch individual status (individual=%s): %s",
                    individual_id, exc,
                )

            # Map to internal status if overall_status is present in report
            if overall_status:
                mapped_report_status = map_ongrid_status(overall_status)
                if mapped_report_status != bgv_record.status:
                    bgv_record.status = mapped_report_status
                    if "status" not in update_fields:
                        update_fields.append("status")

            final_status = bgv_record.status

            # -------------------------------------------------
            # Update status only if changed
            # -------------------------------------------------
            if final_status != old_status:
                if "status" not in update_fields:
                    update_fields.append("status")

                # Terminal statuses
                if final_status in [
                    "completed",
                    "clear",
                    "verified",
                    "closed",
                ]:
                    bgv_record.completed_at = timezone.now()
                    if "completed_at" not in update_fields:
                        update_fields.append("completed_at")
                    print(f"[BGV POLLER] 🏁 Terminal status reached: {final_status}")

                # Full save to trigger signals
                bgv_record.save()
                print(
                    f"[BGV POLLER] ✅ Status UPDATED: {old_status} → {final_status}"
                )

                logger.info(
                    "BGV status updated for %s: %s → %s",
                    candidate_name,
                    old_status,
                    final_status,
                )

            else:
                # Save only payload changes
                if update_fields:
                    bgv_record.save(update_fields=update_fields)
                print(
                    f"[BGV POLLER] Status unchanged ({old_status}). "
                    f"Saved payload updates: {update_fields}"
                )

        print(
            f"\n[BGV POLLER] ====== Poll complete. Processed {len(active_bgvs)} records. ======"
        )

    except Exception as exc:
        print(f"[BGV POLLER] ❌❌❌ EXCEPTION during BGV poll: {exc}")
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

def run_bgv_status_poll_and_reschedule():
    """
    Run the BGV status poll and reschedule after 1 hour.
    The reschedule always happens, even if the poll itself fails,
    so the polling chain never silently dies.
    """

    from onboarding.utils.task_queue import TASK_QUEUE

    print("[BGV POLLER] run_bgv_status_poll_and_reschedule() invoked.")

    try:
        run_bgv_status_poll()
        print("[BGV POLLER] run_bgv_status_poll() completed successfully.")
    except Exception as exc:
        print(f"[BGV POLLER] ❌ run_bgv_status_poll() raised exception: {exc}")
        logger.exception(
            "[BGV POLLER] Error during BGV status poll: %s", exc
        )

    # Always reschedule, regardless of success/failure
    print("[BGV POLLER] Scheduling next poll in 3600 seconds (1 hour)...")
    timer = threading.Timer(
        3600,
        lambda: TASK_QUEUE.enqueue(
            run_bgv_status_poll_and_reschedule
        ),
    )
    timer.daemon = True
    timer.start()
    print("[BGV POLLER] Next poll timer started.")


def schedule_periodic_bgv_status_poll():
    """
    Initial entry point: enqueue the first poll-and-reschedule cycle.
    """

    from onboarding.utils.task_queue import TASK_QUEUE

    print("[BGV POLLER] schedule_periodic_bgv_status_poll() called. Enqueuing first poll...")
    TASK_QUEUE.enqueue(run_bgv_status_poll_and_reschedule)

    print(
        "[BGV POLLER] "
        "Periodic BGV status poll registered. First poll enqueued to TASK_QUEUE."
    )