from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

@receiver(pre_save)
def update_timestamp(sender, instance, **kwargs):
    # Check if the instance has an 'updated_at' field
    if hasattr(instance, 'updated_at'):
        # Only update if it's not a new instance OR if you want it to always update
        # If the user is saving from Admin, instance.updated_at will be set to whatever is in the form.
        # To allow manual overrides, we could check if it has changed, but that requires a DB query.
        # For now, we will set it to now() to fix the "remains same" problem.
        instance.updated_at = timezone.now()
