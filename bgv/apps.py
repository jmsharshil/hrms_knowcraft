from django.apps import AppConfig


class BgvConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bgv'
    _poller_started = False  # Class-level flag to prevent duplicate starts

    def ready(self):
        import bgv.signals  # noqa: F401

        # Prevent schedulers during tests
        import sys
        if 'test' in sys.argv:
            return

        # Prevent duplicate starts (e.g. if ready() is called twice)
        if BgvConfig._poller_started:
            print("[BGV APP] Poller already started, skipping duplicate.")
            return

        # Only start in the main process (avoids double execution in dev server)
        import os

        # Django dev server sets RUN_MAIN=true in the reloader child process.
        # In production (gunicorn), RUN_MAIN is not set at all.
        # We skip only when RUN_MAIN exists but is NOT 'true' (i.e. the parent process).
        run_main = os.environ.get('RUN_MAIN')
        werkzeug_main = os.environ.get('WERKZEUG_RUN_MAIN')

        is_main_process = (
            run_main == 'true' or              # Django dev server reloader child
            werkzeug_main == 'true' or          # Werkzeug dev server
            (run_main is None and werkzeug_main is None)  # Production (gunicorn, etc.)
        )

        print(
            f"[BGV APP] ready() called. "
            f"RUN_MAIN={os.environ.get('RUN_MAIN')}, "
            f"SERVER_SOFTWARE={os.environ.get('SERVER_SOFTWARE')}, "
            f"is_main_process={is_main_process}"
        )

        if is_main_process:
            BgvConfig._poller_started = True
        else:
            print("[BGV APP] Not main process, skipping BGV initialization.")