from django.apps import AppConfig


class MrfConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mrf'

    def ready(self):
        import sys
        if 'test' in sys.argv:
            return
        import mrf.signals