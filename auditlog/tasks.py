"""
Background task that periodically flushes un-synced AuditLog entries
to Azure Blob Storage, organized by company/user/date.

Uses the project's existing BackgroundTaskQueue for scheduling.
"""

import logging
import threading
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

# How many un-flushed logs to process per batch
BATCH_SIZE = 500

# How often the flush task re-schedules itself (seconds)
FLUSH_INTERVAL = 300  # 5 minutes


def _serialise_log(log_obj) -> dict:
    """Convert an AuditLog model instance into a log-safe dict."""
    return {
        "id": str(log_obj.id),
        "user_id": str(log_obj.user_id) if log_obj.user_id else None,
        "user_email": log_obj.user.email if log_obj.user else None,
        "user_name": log_obj.user.name if log_obj.user else None,
        "user_role": log_obj.user.role if log_obj.user else None,
        "company_id": str(log_obj.company_id) if log_obj.company_id else None,
        "action": log_obj.action,
        "method": log_obj.method,
        "path": log_obj.path,
        "endpoint_name": log_obj.endpoint_name,
        "status_code": log_obj.status_code,
        "query_params": log_obj.query_params,
        "request_body": log_obj.request_body,
        "response_summary": log_obj.response_summary,
        "ip_address": log_obj.ip_address,
        "user_agent": log_obj.user_agent,
        "target_model": log_obj.target_model,
        "target_id": log_obj.target_id,
        "timestamp": log_obj.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log_obj.timestamp else "",
    }


def flush_logs_to_blob():
    """
    Find all AuditLog entries where flushed_to_blob=False,
    group them by (company, user, date), upload each group
    as a .log file to Azure Blob Storage, then mark them as flushed.
    """
    from .models import AuditLog
    from .blob_service import upload_log_file

    print("[AUDIT FLUSH] Starting blob flush...")

    try:
        unflushed = list(
            AuditLog.objects.filter(flushed_to_blob=False)
            .select_related("user", "company")
            .order_by("timestamp")[:BATCH_SIZE]
        )

        if not unflushed:
            print("[AUDIT FLUSH] No un-flushed logs found.")
            return

        # Group by (company_id, user_id, date)
        groups = defaultdict(list)
        for log_obj in unflushed:
            company_id = str(log_obj.company_id) if log_obj.company_id else "unknown_company"
            user_id = str(log_obj.user_id) if log_obj.user_id else "anonymous"
            log_date = log_obj.timestamp.date()
            key = (company_id, user_id, log_date)
            groups[key].append(log_obj)

        # Upload each group
        success_ids = []
        for (company_id, user_id, log_date), logs in groups.items():
            entries = [_serialise_log(obj) for obj in logs]
            ok = upload_log_file(company_id, user_id, log_date, entries)
            if ok:
                success_ids.extend([obj.id for obj in logs])
            else:
                logger.warning(
                    "[AUDIT FLUSH] Skipping mark for %d logs in %s/%s/%s due to upload failure",
                    len(logs), company_id, user_id, log_date,
                )

        # Mark flushed logs
        if success_ids:
            updated = AuditLog.objects.filter(id__in=success_ids).update(flushed_to_blob=True)
            print(f"[AUDIT FLUSH] Marked {updated} logs as flushed.")

        print(
            f"[AUDIT FLUSH] Processed {len(unflushed)} logs in {len(groups)} groups."
        )

    except Exception as exc:
        logger.exception("[AUDIT FLUSH] Error during flush: %s", exc)


def flush_logs_and_reschedule():
    """
    Run the flush once and then reschedule itself after FLUSH_INTERVAL seconds.
    """
    flush_logs_to_blob()

    from onboarding.utils.task_queue import TASK_QUEUE

    timer = threading.Timer(
        FLUSH_INTERVAL,
        lambda: TASK_QUEUE.enqueue(flush_logs_and_reschedule),
    )
    timer.daemon = True
    timer.start()


def schedule_periodic_flush():
    """
    Entry point: called once from AppConfig.ready() to start the periodic flush.
    """
    from onboarding.utils.task_queue import TASK_QUEUE

    TASK_QUEUE.enqueue(flush_logs_and_reschedule)

    print("[AUDIT FLUSH] Periodic audit log flush registered.")
