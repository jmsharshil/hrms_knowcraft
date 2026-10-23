# automation/task_queue.py
import threading
import queue
import time
import logging

logger = logging.getLogger(__name__)

class BackgroundTaskQueue:
    def __init__(self, worker_count=2, max_retries=5):
        self.queue = queue.Queue()
        self.max_retries = max_retries

        for i in range(worker_count):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            logger.info(f"[TASK] Worker-{i+1} started")

    def enqueue(self, fn, *args, **kwargs):
        self.queue.put({"fn": fn, "args": args, "kwargs": kwargs, "attempt": 1})

    def _worker(self):
        from django.db import close_old_connections

        while True:
            task = self.queue.get()

            fn = task["fn"]
            args = task["args"]
            kwargs = task["kwargs"]
            attempt = task["attempt"]
            fn_name = getattr(fn, "__name__", str(fn))

            try:
                close_old_connections()
                fn(*args, **kwargs)
                logger.info(f"[TASK] Completed {fn_name}")
            except Exception as e:
                logger.error(f"[TASK] Failed {fn_name}: {e}", exc_info=True)
                close_old_connections()

                if attempt < self.max_retries:
                    task["attempt"] += 1
                    logger.info(f"[TASK] Retrying {fn_name} ({attempt}/{self.max_retries})...")
                    time.sleep(2 ** attempt)
                    self.queue.put(task)
                else:
                    logger.error(f"[TASK] Max retries reached for {fn_name}")
            finally:
                close_old_connections()
                self.queue.task_done()


# global background queue
TASK_QUEUE = BackgroundTaskQueue(worker_count=3, max_retries=5)
