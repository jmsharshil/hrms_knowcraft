from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from scheduler.services import TaskScheduler


class SchedulerCoordinatorTests(SimpleTestCase):
    @patch("scheduler.services.transaction.atomic")
    @patch("scheduler.services.connection")
    def test_runs_callback_when_database_lock_is_acquired(
        self, connection_mock, atomic_mock
    ):
        connection_mock.vendor = "postgresql"
        cursor = MagicMock()
        cursor.fetchone.return_value = (True,)
        connection_mock.cursor.return_value.__enter__.return_value = cursor
        callback = MagicMock()

        acquired = TaskScheduler.run_if_coordinator(callback)

        self.assertTrue(acquired)
        callback.assert_called_once_with()
        cursor.execute.assert_called_once()

    @patch("scheduler.services.transaction.atomic")
    @patch("scheduler.services.connection")
    def test_skips_callback_when_another_worker_holds_lock(
        self, connection_mock, _atomic_mock
    ):
        connection_mock.vendor = "postgresql"
        cursor = MagicMock()
        cursor.fetchone.return_value = (False,)
        connection_mock.cursor.return_value.__enter__.return_value = cursor
        callback = MagicMock()

        acquired = TaskScheduler.run_if_coordinator(callback)

        self.assertFalse(acquired)
        callback.assert_not_called()

    @patch("scheduler.services.connection")
    def test_requires_postgresql_for_multi_worker_coordination(self, connection_mock):
        connection_mock.vendor = "sqlite"

        with self.assertRaisesRegex(RuntimeError, "requires PostgreSQL"):
            TaskScheduler.run_if_coordinator(MagicMock())


class ReconcileTests(SimpleTestCase):
    @patch("scheduler.models.ScheduledTask.objects.filter")
    @patch.object(TaskScheduler, "_schedule_in_memory")
    def test_reconcile_only_requeues_overdue_pending_tasks(self, schedule, filter_tasks):
        filter_tasks.return_value.values_list.return_value = ["pending-task"]

        TaskScheduler.reconcile()

        self.assertEqual(filter_tasks.call_count, 1)
        self.assertEqual(filter_tasks.call_args.kwargs["status"], "pending")
        schedule.assert_called_once_with("pending-task", delay_seconds=0)
