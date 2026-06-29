from django.apps import AppConfig


class OnboardingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "onboarding"

    def ready(self):
        """Signals only — TaskScheduler is initialized in scheduler/apps.py
        (registers interview_feedback_reminder + all other tasks, ensures
        recurring system tasks, runs reconcile/reschedule in main process
        after full Django startup, with test/main-process guards).
        """
        import onboarding.signals
