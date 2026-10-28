# scheduler/management/commands/reconcile_tasks.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from scheduler.services import TaskScheduler
from scheduler.models import ScheduledTask


class Command(BaseCommand):
    help = "Force reconciliation of all overdue and stuck background scheduled tasks."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(f"[{timezone.now()}] Starting task reconciliation..."))

        sched_app = apps.get_app_config("scheduler")

        def reconcile():
            sched_app._ensure_recurring_tasks()
            TaskScheduler.reconcile()
            TaskScheduler.reschedule_future_pending()

        try:
            coordinated = TaskScheduler.run_if_coordinator(reconcile)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Reconciliation failed: {e}"))
            return

        if not coordinated:
            self.stdout.write(self.style.WARNING("Another worker is currently reconciling tasks."))
            return

        now = timezone.now()
        pending = ScheduledTask.objects.filter(status="pending").count()
        overdue = ScheduledTask.objects.filter(status="pending", scheduled_at__lte=now).count()
        running = ScheduledTask.objects.filter(status="running").count()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Reconciliation complete. Status: pending={pending} (overdue={overdue}), running={running}"
            )
        )
