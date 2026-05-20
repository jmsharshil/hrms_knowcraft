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


def run_bgv_schedule_check_and_reschedule():
    """
    Task that runs the BGV schedule check and reschedules itself
    to run again in 1 hour.
    """
    from onboarding.utils.task_queue import TASK_QUEUE

    run_bgv_schedule_check()

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
    print("[BGV SCHEDULER] Periodic BGV schedule check registered.")
