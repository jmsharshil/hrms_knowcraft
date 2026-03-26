from django.apps import AppConfig
from onboarding.utils.task_queue import TASK_QUEUE

class BookingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booking'

    def ready(self):
        import booking.signals
        # TASK_QUEUE.enqueue(self._init_subscriptions)

    # def _init_subscriptions(self):
    #     # Import here to avoid import-time ORM access
    #     from .utils import init_graph_subscriptions, periodic_subscription_renewal

    #     # ⚡ Initialize subscriptions
    #     init_graph_subscriptions()

    #     # ⚡ Optionally start periodic renewal task
    #     periodic_subscription_renewal()