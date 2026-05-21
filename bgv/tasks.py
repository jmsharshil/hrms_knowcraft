# bgv/tasks.py

"""
Periodic background task that checks for experienced candidates
whose BGV scheduled date has arrived (15 days before joining),
and initiates their BGV process via OnGrid.

Follows the same pattern as onboarding/utils/joining_check.py.
"""

import logging
import threading
from datetime import date

logger = logging.getLogger(__name__)


def run_bgv_schedule_check():
    """
    Find all CandidateBGV records with status='pending_schedule'
    whose bgv_scheduled_date <= today, and initiate BGV for them.
    """
    from .models import CandidateBGV
    from .services import initiate_bgv

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
                f"[BGV SCHEDULER] Initiating BGV for experienced candidate "
                f"{candidate.candidate_name} (app={candidate.id}, "
                f"scheduled={bgv_record.bgv_scheduled_date})"
            )
            try:
                initiate_bgv(candidate)
                logger.info(
                    "BGV initiated for scheduled candidate %s (app=%s)",
                    candidate.candidate_name, candidate.id,
                )
            except Exception as exc:
                logger.exception(
                    "Failed to initiate scheduled BGV for %s (app=%s): %s",
                    candidate.candidate_name, candidate.id, exc,
                )

        print(
            f"[BGV SCHEDULER] Processed {len(pending_bgvs)} scheduled BGV records."
        )

    except Exception as exc:
        logger.error("[BGV SCHEDULER] Error during scheduled BGV check: %s", exc)


def run_bgv_status_poll():
    """
    Find all CandidateBGV records with status in ('initiated', 'in_progress')
    and poll the OnGrid API for their latest status.

    Only saves when a status change is detected to avoid triggering
    unnecessary post_save signals (and duplicate HR notifications).
    """
    from django.utils import timezone
    from .models import CandidateBGV
    from .services import get_verification_report, get_individual_status

    print("[BGV POLLER] Starting check for in-progress BGV records...")

    try:
        active_bgvs = list(
            CandidateBGV.objects.filter(
                status__in=["initiated", "in_progress"]
            )
            .exclude(ongrid_individual_id="")
            .exclude(ongrid_individual_id__isnull=True)
            .select_related("candidate")
        )

        if not active_bgvs:
            print("[BGV POLLER] No active BGV records to poll.")
            return

        for bgv_record in active_bgvs:
            print(f"[BGV POLLER] Polling status for {bgv_record.candidate.candidate_name} ({bgv_record.ongrid_individual_id})")
            
            report = get_verification_report(bgv_record.ongrid_individual_id)
            if not report:
                continue

            old_status = bgv_record.status
            update_fields = []

            # Always update the callback payload with latest data
            bgv_record.callback_payload = report
            update_fields.append("callback_payload")

            # Check if verifications are concluded
            verifications = report.get("verifications", [])

            if not verifications:
                # Save payload update only, skip status logic
                bgv_record.save(update_fields=update_fields)
                continue

            all_completed = True
            any_insufficient = False

            for ver in verifications:
                v_status = ver.get("status", "")
                if v_status == "DataInsufficient":
                    any_insufficient = True
                elif v_status not in ("Clear", "Discrepancy", "Completed", "UnableToVerify"):
                    all_completed = False

            # Determine new status
            if any_insufficient:
                new_status = "insufficient"
            elif all_completed:
                new_status = "completed"
            else:
                new_status = "in_progress"

            # Only update status-related fields if status actually changed
            if new_status != old_status:
                bgv_record.status = new_status
                update_fields.append("status")

                if new_status == "completed":
                    bgv_record.completed_at = timezone.now()
                    update_fields.append("completed_at")

                # Try to extract report URL from individual status
                try:
                    individual_data = get_individual_status(bgv_record.ongrid_individual_id)
                    if individual_data:
                        report_url = individual_data.get("reportUrl") or individual_data.get("report_url")
                        if report_url:
                            bgv_record.report_url = report_url
                            update_fields.append("report_url")
                except Exception:
                    logger.warning(
                        "Failed to fetch individual status for report URL (individual=%s)",
                        bgv_record.ongrid_individual_id,
                    )

                # Use full save() to trigger post_save signal (for HR notifications)
                bgv_record.save()
            else:
                # No status change — save payload only without triggering signals
                bgv_record.save(update_fields=update_fields)

        print(f"[BGV POLLER] Polled {len(active_bgvs)} BGV records.")

    except Exception as exc:
        logger.error("[BGV POLLER] Error during BGV poll: %s", exc)


def run_bgv_schedule_check_and_reschedule():
    """
    Task that runs the BGV schedule check and reschedules itself
    to run again in 1 hour.
    """
    from onboarding.utils.task_queue import TASK_QUEUE

    run_bgv_schedule_check()
    run_bgv_status_poll()

    # Reschedule after 1 hour (3600 seconds)
    timer = threading.Timer(
        3600,
        lambda: TASK_QUEUE.enqueue(run_bgv_schedule_check_and_reschedule),
    )
    timer.daemon = True
    timer.start()


def schedule_periodic_bgv_check():
    """
    Initial entry point — enqueues the first BGV check into the task queue.
    Called from bgv/apps.py on startup.
    """
    from onboarding.utils.task_queue import TASK_QUEUE

    TASK_QUEUE.enqueue(run_bgv_schedule_check_and_reschedule)
    print("[BGV SCHEDULER] Periodic BGV schedule & poll check registered.")
