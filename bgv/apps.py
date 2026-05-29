from django.apps import AppConfig


class BgvConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bgv'

    def ready(self):
        import bgv.signals  # noqa: F401

        # Prevent schedulers during tests
        import sys
        if 'test' in sys.argv:
            return

        # Only start in the main process (avoids double execution in dev server)
        import os
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            # Start the periodic BGV schedule checker (for experienced candidates)
            from .tasks import schedule_periodic_bgv_check
            # schedule_periodic_bgv_check()
