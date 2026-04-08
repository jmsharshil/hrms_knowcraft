from django.utils import timezone

from django.apps import AppConfig
import time
import threading

class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

    def ready(self):
        import jobs.signals
        if not hasattr(self, '_expiry_thread_started'):
            self._expiry_thread_started = True

            def expiry_monitor():
                """
                Daemon thread: Runs close_expired_jobs every INTERVAL seconds.
                """
                INTERVAL = 24 * 60 * 60  # 24 hours; adjust for testing (e.g., 60 for 1 min)
                while True:
                    try:
                        time.sleep(INTERVAL)
                        from .models import Job
                        closed, apps = Job.close_expired_jobs()
                        print(f'Background thread: Processed {closed} jobs, {apps} apps at {timezone.now()}')
                    except Exception as e:
                        print(f'Expiry monitor error: {e}')  # Log error, continue running
                        # Optional: time.sleep(60) to retry sooner on error

            # Start as daemon thread
            thread = threading.Thread(target=expiry_monitor, daemon=True)
            thread.start()
            print('Expiry monitoring thread started.')