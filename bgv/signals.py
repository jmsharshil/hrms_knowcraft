# bgv/signals.py

import logging
from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver

from jobs.models import JobApplication

from .models import CandidateBGV
from .services import initiate_bgv, is_fresher


logger = logging.getLogger(__name__)


@receiver(post_save, sender=JobApplication)
def trigger_bgv_on_offer_accepted(sender, instance, created, **kwargs):
    """
    Auto-trigger BGV when a JobApplication moves to 'offer_accepted' status.

    Logic:
    - Freshers (experience < 1 year): Initiate BGV immediately via OnGrid API
    - Experienced (experience >= 1 year): Schedule BGV for 15 days before
      the candidate's joining_date. A periodic task will pick this up.

    Skips if a BGV record already exists for this candidate (unless it failed).
    """

    if created:
        return

    if instance.status != "offer_accepted":
        return

    # Allow re-initiation only if the previous attempt failed
    existing_bgv = CandidateBGV.objects.filter(candidate=instance).first()
    if existing_bgv and existing_bgv.status not in ("failed",):
        logger.info(
            "BGV already exists for application %s (status=%s), skipping.",
            instance.id, existing_bgv.status,
        )
        return

    fresher = is_fresher(instance)

    if fresher:
        # ── Fresher: Initiate BGV immediately ────────────────
        logger.info(
            "Fresher candidate %s – initiating BGV immediately.",
            instance.candidate_name,
        )
        try:
            initiate_bgv(instance)
        except Exception:
            logger.exception(
                "Failed to auto-initiate BGV for fresher application %s",
                instance.id,
            )
    else:
        # ── Experienced: Schedule BGV 15 days before joining ─
        joining_date = instance.joining_date
        if joining_date:
            scheduled_date = joining_date - timedelta(days=15)
            logger.info(
                "Experienced candidate %s – scheduling BGV for %s "
                "(15 days before joining date %s).",
                instance.candidate_name, scheduled_date, joining_date,
            )
        else:
            # No joining date yet – create record as pending,
            # it will be picked up when joining_date is set
            scheduled_date = None
            logger.info(
                "Experienced candidate %s – no joining date set, "
                "creating pending BGV record.",
                instance.candidate_name,
            )

        try:
            CandidateBGV.objects.update_or_create(
                candidate=instance,
                defaults={
                    "status": "pending_schedule",
                    "bgv_scheduled_date": scheduled_date,
                    "is_fresher": False,
                    "remarks": (
                        f"Scheduled for {scheduled_date}" if scheduled_date
                        else "Waiting for joining date to be set"
                    ),
                },
            )
        except Exception:
            logger.exception(
                "Failed to create scheduled BGV record for application %s",
                instance.id,
            )


@receiver(post_save, sender=JobApplication)
def update_bgv_schedule_on_joining_date_change(sender, instance, created, **kwargs):
    """
    When a candidate's joining_date is updated, recalculate the
    bgv_scheduled_date for experienced candidates with pending BGV.
    """
    if created:
        return

    if not instance.joining_date:
        return

    try:
        bgv = CandidateBGV.objects.get(
            candidate=instance,
            status="pending_schedule",
            is_fresher=False,
        )
    except CandidateBGV.DoesNotExist:
        return

    new_scheduled_date = instance.joining_date - timedelta(days=15)

    if bgv.bgv_scheduled_date != new_scheduled_date:
        bgv.bgv_scheduled_date = new_scheduled_date
        bgv.remarks = f"Rescheduled for {new_scheduled_date} (joining date: {instance.joining_date})"
        bgv.save(update_fields=["bgv_scheduled_date", "remarks"])
        logger.info(
            "Updated BGV schedule for %s to %s (joining date changed to %s)",
            instance.candidate_name, new_scheduled_date, instance.joining_date,
        )