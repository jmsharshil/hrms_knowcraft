from django.apps import AppConfig


class BgvConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bgv'

    def ready(self):
        import bgv.signals  # noqa: F401

        # Start the periodic BGV schedule checker (for experienced candidates)
        from .tasks import schedule_periodic_bgv_check
        schedule_periodic_bgv_check()
