import logging
from datetime import date
import threading
import time

logger = logging.getLogger(__name__)

def run_joining_date_check():
    """
    Check for candidates in 'joining_pending' whose joining date is today or in the past,
    and transition them to 'joined'.

    Called periodically by the persistent TaskScheduler (recurring every 3600s).
    Returns True to keep the recurring task alive.
    """
    from jobs.models import JobApplication
    from onboarding.utils.engine import automation_engine
    print("[JOINING CHECK] Starting background check for joining dates...")
    try:
        # Find candidates whose joining date has arrived
        apps_to_update = list(JobApplication.objects.filter(
            status='joining_pending',
            joining_date__lte=date.today()
        ))
        
        if not apps_to_update:
            print("[JOINING CHECK] No candidates found for transition.")
            return True

        from django.db import transaction
        for app in apps_to_update:
            with transaction.atomic():
                locked_app = JobApplication.objects.select_for_update(skip_locked=True).filter(
                    id=app.id,
                    status='joining_pending'
                ).first()
                if not locked_app:
                    continue
                print(f"[JOINING CHECK] Auto-transitioning {locked_app.candidate_name} (ID: {locked_app.id}) to joined")
                # automation_engine will handle status change, notifications, Job/MRF sync
                ok, reason = automation_engine(locked_app, 'joining_pending', 'joined')
                if not ok:
                    logger.warning(f"Transition failed for {locked_app.id}: {reason}")
        print(f"[JOINING CHECK] Successfully processed {len(apps_to_update)} candidates.")
        return True
    except Exception as e:
        logger.error(f"[JOINING CHECK] Error during background joining check: {e}")

    return True  # Keep the recurring task alive even if there was an error

# def schedule_periodic_joining_check():
#     """
#     Schedules the check to run periodically using the global TASK_QUEUE.
#     """
#     from .task_queue import TASK_QUEUE
    
#     def task_wrapper():
#         # Execute the check
#         run_joining_date_check()
        
#         # Schedule the next run in 1 hour
#         # We use threading.Timer to avoid blocking the current TASK_QUEUE worker
#         threading.Timer(3600, schedule_next).start()

#     def schedule_next():
#         TASK_QUEUE.enqueue(run_joining_date_check_and_reschedule)

#     # We use a separate function that both runs and reschedules to keep it in the queue flow
#     TASK_QUEUE.enqueue(run_joining_date_check_and_reschedule)

# def run_joining_date_check_and_reschedule():
#     """
#     Task that runs the check and then schedules itself again.
#     """
#     from .task_queue import TASK_QUEUE
    
#     run_joining_date_check()
    
#     # Wait for 1 hour then enqueue again
#     # Note: We use a daemon thread for the timer to not block shutdown
#     timer = threading.Timer(3600, lambda: TASK_QUEUE.enqueue(run_joining_date_check_and_reschedule))
#     timer.daemon = True
#     timer.start()
