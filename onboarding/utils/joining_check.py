import logging
from datetime import date
import threading
import time

logger = logging.getLogger(__name__)

def run_joining_date_check():
    """
    Check for candidates in 'joining_pending' whose joining date is today or in the past,
    and transition them to 'joined'.
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
            return

        for app in apps_to_update:
            print(f"[JOINING CHECK] Auto-transitioning {app.candidate_name} (ID: {app.id}) to joined")
            # automation_engine will handle status change and Job/MRF updates
            ok,reason = automation_engine(app, 'joining_pending', 'joined')
            if ok:                
                # Update job positions_filled
                job = app.job
                if job.positions_filled < job.no_of_positions:
                    job.positions_filled += 1
                    job.save(update_fields=['positions_filled'])
                    
                    if job.positions_filled >= job.no_of_positions:
                        job.status = 'filled'
                        job.save(update_fields=['status'])
                        
                        # Sync to MRF
                        if hasattr(job, 'mrf') and job.mrf:
                            mrf = job.mrf
                            if mrf.status != 'filled':
                                mrf.status = 'filled'
                                mrf.save(update_fields=['status'])
            
        print(f"[JOINING CHECK] Successfully processed {len(apps_to_update)} candidates.")
    except Exception as e:
        logger.error(f"[JOINING CHECK] Error during background joining check: {e}")

def schedule_periodic_joining_check():
    """
    Schedules the check to run periodically using the global TASK_QUEUE.
    """
    from .task_queue import TASK_QUEUE
    
    def task_wrapper():
        # Execute the check
        run_joining_date_check()
        
        # Schedule the next run in 1 hour
        # We use threading.Timer to avoid blocking the current TASK_QUEUE worker
        threading.Timer(3600, schedule_next).start()

    def schedule_next():
        TASK_QUEUE.enqueue(run_joining_date_check_and_reschedule)

    # We use a separate function that both runs and reschedules to keep it in the queue flow
    TASK_QUEUE.enqueue(run_joining_date_check_and_reschedule)

def run_joining_date_check_and_reschedule():
    """
    Task that runs the check and then schedules itself again.
    """
    from .task_queue import TASK_QUEUE
    
    run_joining_date_check()
    
    # Wait for 1 hour then enqueue again
    # Note: We use a daemon thread for the timer to not block shutdown
    timer = threading.Timer(3600, lambda: TASK_QUEUE.enqueue(run_joining_date_check_and_reschedule))
    timer.daemon = True
    timer.start()
