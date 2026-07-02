# scheduler/admin.py

from django.contrib import admin
from .models import ScheduledTask
from django.utils import timezone
from .services import TaskScheduler


@admin.action(description="Cancel (Stop) selected tasks")
def cancel_tasks(modeladmin, request, queryset):
    # Update pending tasks
    updated = queryset.filter(status="pending").update(
        status="cancelled", updated_at=timezone.now()
    )
    modeladmin.message_user(request, f"Successfully cancelled {updated} pending tasks.")


@admin.action(description="Restart / Retry selected tasks immediately")
def restart_tasks(modeladmin, request, queryset):
    # Allow restarting failed, cancelled, or completed tasks
    tasks = queryset.filter(status__in=["failed", "cancelled", "completed", "pending"])
    count = 0
    now = timezone.now()
    for task in tasks:
        task.status = "pending"
        task.retry_count = 0
        task.scheduled_at = now
        task.started_at = None
        task.completed_at = None
        task.error_message = None
        task.save()
        TaskScheduler._schedule_in_memory(task.id, 0)
        count += 1
    modeladmin.message_user(request, f"Successfully restarted {count} tasks.")


@admin.action(description="🛑 Cancel ALL feedback reminders (pending + running)")
def cancel_all_feedback_reminders(modeladmin, request, queryset):
    """
    Bulk-cancel every pending AND running interview_feedback_reminder task.
    This is independent of the queryset selection — it cancels ALL of them.
    Useful when reminders are misbehaving and you need an emergency stop.
    """
    now = timezone.now()

    # Cancel pending
    pending_count = ScheduledTask.objects.filter(
        task_type="interview_feedback_reminder",
        status="pending",
    ).update(status="cancelled", updated_at=now)

    # Cancel running (prevents reschedule after current execution)
    running_count = ScheduledTask.objects.filter(
        task_type="interview_feedback_reminder",
        status="running",
    ).update(status="cancelled", updated_at=now)

    # Clear armed task IDs so in-memory timers are ignored when they fire
    cancelled_ids = list(
        ScheduledTask.objects.filter(
            task_type="interview_feedback_reminder",
            status="cancelled",
        ).values_list("id", flat=True)
    )
    for tid in cancelled_ids:
        TaskScheduler._armed_task_ids.discard(tid)

    total = pending_count + running_count
    modeladmin.message_user(
        request,
        f"🛑 Cancelled {total} feedback reminder task(s) "
        f"({pending_count} pending, {running_count} running)."
    )


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    actions = [cancel_tasks, restart_tasks, cancel_all_feedback_reminders]
    list_display = [
        "task_type",
        "status",
        "scheduled_at",
        "started_at",
        "completed_at",
        "is_recurring",
        "interval_seconds",
        "retry_count",
        "created_at",
    ]
    list_filter = ["status", "task_type", "is_recurring"]
    search_fields = ["task_type", "id"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "started_at",
        "completed_at",
    ]
    ordering = ["-created_at"]

