from django.apps import AppConfig


class MrfConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mrf'

    def ready(self):
        import sys
        ignored_commands = ["test", "makemigrations", "migrate", "showmigrations"]
        if any(cmd in sys.argv for cmd in ignored_commands):
            return
        import mrf.signals