# scheduler/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import ScheduledTask
from .services import TaskScheduler


class TaskCancelView(APIView):
    """
    Cancel a pending scheduled task.
    """
    def post(self, request, task_id):
        task = get_object_or_404(ScheduledTask, id=task_id)
        
        if task.status != "pending":
            return Response(
                {"detail": f"Task cannot be cancelled because it is {task.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        task.status = "cancelled"
        task.updated_at = timezone.now()
        task.save(update_fields=["status", "updated_at"])
        
        return Response({"detail": "Task cancelled successfully."})


class TaskRestartView(APIView):
    """
    Restart a failed, cancelled, completed, or even pending task immediately.
    """
    def post(self, request, task_id):
        task = get_object_or_404(ScheduledTask, id=task_id)
        
        if task.status == "running":
            return Response(
                {"detail": "Task is currently running and cannot be restarted."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        task.status = "pending"
        task.retry_count = 0
        task.scheduled_at = timezone.now()
        task.started_at = None
        task.completed_at = None
        task.error_message = None
        task.save()
        
        # Enqueue it immediately
        TaskScheduler._schedule_in_memory(task.id, delay_seconds=0)
        
        return Response({"detail": "Task restarted successfully."})


class TaskReconcileView(APIView):
    """
    Force an immediate reconciliation of overdue pending tasks.
    Also ensures recurring tasks exist.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from django.apps import apps
        from django.db import close_old_connections

        sched_app = apps.get_app_config("scheduler")

        def reconcile():
            sched_app._ensure_recurring_tasks()
            TaskScheduler.reconcile()
            TaskScheduler.reschedule_future_pending()

        try:
            close_old_connections()
            coordinated = TaskScheduler.run_if_coordinator(reconcile)
        except Exception:
            import logging

            logging.getLogger(__name__).exception("Manual task reconciliation failed.")
            return Response(
                {"detail": "Task reconciliation failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            close_old_connections()

        if not coordinated:
            return Response(
                {"detail": "Another worker is currently reconciling tasks."},
                status=status.HTTP_409_CONFLICT,
            )

        now = timezone.now()
        pending_count = ScheduledTask.objects.filter(status="pending").count()
        overdue_count = ScheduledTask.objects.filter(status="pending", scheduled_at__lte=now).count()
        running_count = ScheduledTask.objects.filter(status="running").count()

        return Response({
            "detail": "Reconciliation completed successfully.",
            "pending_count": pending_count,
            "overdue_count": overdue_count,
            "running_count": running_count,
        })


class TaskSummaryView(APIView):
    """
    Get summary statistics and health status of background scheduled tasks.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.db import models, close_old_connections
        close_old_connections()
        now = timezone.now()

        status_counts = dict(
            ScheduledTask.objects.values_list("status")
            .annotate(count=models.Count("id"))
        )

        overdue_queryset = ScheduledTask.objects.filter(
            status="pending", scheduled_at__lte=now
        )
        overdue_count = overdue_queryset.count()
        overdue_tasks = list(
            overdue_queryset
            .values("id", "task_type", "scheduled_at", "retry_count")[:20]
        )

        recurring_tasks = list(
            ScheduledTask.objects.filter(is_recurring=True)
            .order_by("task_type", "-created_at")
            .values("task_type", "status", "scheduled_at", "completed_at", "error_message")[:20]
        )

        return Response({
            "status_counts": status_counts,
            "overdue_pending_count": overdue_count,
            "overdue_sample": overdue_tasks,
            "recurring_tasks_sample": recurring_tasks,
            "registered_task_types": list(TaskScheduler._registry.keys()),
            "server_time": now.isoformat(),
        })
