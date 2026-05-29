from django.apps import AppConfig


class OnboardingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'onboarding'

    def ready(self):
        import onboarding.signals
        
        # Start the background thread for periodic joining date checks
        from .utils.joining_check import run_joining_date_check_and_reschedule
        from .utils.task_queue import TASK_QUEUE
        import os

        # Prevent schedulers during tests
        import sys
        if 'test' in sys.argv:
            return

        # Only start in the main process (avoids double execution in dev server)
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            TASK_QUEUE.enqueue(run_joining_date_check_and_reschedule)
