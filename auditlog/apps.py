from django.apps import AppConfig


class AuditlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auditlog'

    def ready(self):
        import auditlog.signals  # noqa: F401

        # Start the background periodic flush to blob storage
        import os
        import sys

        # Prevent during tests
        if 'test' in sys.argv:
            return

        # Only start in the main process (avoids double execution in dev server)
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            from .tasks import schedule_periodic_flush
            schedule_periodic_flush()
