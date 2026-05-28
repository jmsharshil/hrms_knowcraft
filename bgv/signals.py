# bgv/signals.py

import logging
from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from jobs.models import JobApplication
from onboarding.models import ApprovalNote

from .models import CandidateBGV
from .services import initiate_bgv, is_fresher


logger = logging.getLogger(__name__)

FRONTEND_URL = getattr(settings, "FRONTEND_URL", "http://localhost:3000")


# ── HR Notification helpers ──────────────────────────────────────

BGV_STATUS_DISPLAY = {
    "initiated": "BGV Initiated",
    "in_progress": "BGV In Progress",
    "completed": "BGV Completed",
    "insufficient": "BGV Data Insufficient",
    "failed": "BGV Failed",
}


def _get_assigned_hrs(job):
    """
    Collect all assigned HR users for a job from both the legacy
    ForeignKey and the ManyToMany field. Returns a deduplicated list.
    """
    hr_set = {}

    # Legacy single-assignment FK
    if getattr(job, "assigned_to_internal_hr", None):
        hr = job.assigned_to_internal_hr
        hr_set[str(hr.id)] = hr

    # Multi-assignment M2M
    if hasattr(job, "assigned_internal_hrs"):
        for hr in job.assigned_internal_hrs.all():
            hr_set[str(hr.id)] = hr

    return list(hr_set.values())


def _notify_hr_bgv_status_change(bgv_instance, new_display_status):
    """
    Send email + WhatsApp notification to all assigned HRs of the
    candidate's job when BGV status changes.
    """
    try:
        app = bgv_instance.candidate
        job = app.job

        # Skip notifications for private jobs
        if getattr(job, "is_private", False):
            logger.info(
                "Skipping BGV notification for private job %s", job.id
            )
            return

        hr_users = _get_assigned_hrs(job)
        if not hr_users:
            logger.info(
                "No assigned HR found for job %s – skipping BGV notification.",
                job.id,
            )
            return

        candidate_name = app.candidate_name or "Unknown"
        job_title = job.job_title or "N/A"
        designation = (
            job.designation.name if getattr(job, "designation", None) else "N/A"
        )
        status_label = new_display_status

        subject = f"BGV Status Update: {candidate_name} – {status_label}"

        plain_text = (
            f"Hi,\n\n"
            f"The Background Verification status for the following candidate has been updated:\n\n"
            f"Candidate: {candidate_name}\n"
            f"Position: {job_title} ({designation})\n"
            f"New BGV Status: {status_label}\n"
        )
        if bgv_instance.remarks:
            plain_text += f"Remarks: {bgv_instance.remarks}\n"
        plain_text += (
            f"\nPlease log in to the portal for details:\n"
            f"{FRONTEND_URL}\n\n"
            f"Warm Regards,\nHR Team\nKnowcraft Analytics Private Limited."
        )

        html_template = f"""
<html>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
<table align="center" width="100%" style="max-width:620px;background:#ffffff;border-radius:10px;">
<tr>
<td style="padding:40px;text-align:center;">
<img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:250px;">
</td>
</tr>
<tr>
<td style="padding:30px 40px;color:#333;font-size:16px;line-height:1.6">

<p>Dear HR,</p>

<p>The <b>Background Verification</b> status for the following candidate has been updated:</p>

<table style="width:100%;border-collapse:collapse;margin:20px 0;">
<tr><td style="padding:8px 12px;font-weight:600;background:#f8f9fb;border:1px solid #e6ebf5;">Candidate</td>
    <td style="padding:8px 12px;border:1px solid #e6ebf5;">{candidate_name}</td></tr>
<tr><td style="padding:8px 12px;font-weight:600;background:#f8f9fb;border:1px solid #e6ebf5;">Position</td>
    <td style="padding:8px 12px;border:1px solid #e6ebf5;">{job_title} ({designation})</td></tr>
<tr><td style="padding:8px 12px;font-weight:600;background:#f8f9fb;border:1px solid #e6ebf5;">BGV Status</td>
    <td style="padding:8px 12px;border:1px solid #e6ebf5;"><b>{status_label}</b></td></tr>
{f'<tr><td style="padding:8px 12px;font-weight:600;background:#f8f9fb;border:1px solid #e6ebf5;">Remarks</td><td style="padding:8px 12px;border:1px solid #e6ebf5;">{bgv_instance.remarks}</td></tr>' if bgv_instance.remarks else ''}
</table>

<p style="text-align:center;margin:30px 0;">
<a href="{FRONTEND_URL}"
style="background:#2563eb;color:#fff;padding:14px 28px;border-radius:6px;text-decoration:none;font-weight:600;">
View Details on Portal
</a>
</p>

<br>
<p>Warm Regards,<br>
<b>HR Team</b><br>
<b>Knowcraft Analytics Private Limited.</b>
</p>

</td>
</tr>
</table>
</body>
</html>
"""

        # Lazy import to avoid circular import at module level
        from onboarding.utils.sender import send_email, send_text

        for hr in hr_users:
            try:
                send_email(
                    to=hr.email,
                    subject=subject,
                    text=plain_text,
                    template=html_template,
                )
                logger.info(
                    "BGV status email sent to HR %s (%s) for candidate %s",
                    hr.name, hr.email, candidate_name,
                )
            except Exception:
                logger.exception(
                    "Failed to send BGV email to HR %s (%s)",
                    hr.name, hr.email,
                )

            if getattr(hr, "phone", None):
                try:
                    send_text(to=hr.phone, text=plain_text)
                    logger.info(
                        "BGV status WhatsApp sent to HR %s (%s)",
                        hr.name, hr.phone,
                    )
                except Exception:
                    logger.exception(
                        "Failed to send BGV WhatsApp to HR %s (%s)",
                        hr.name, hr.phone,
                    )

    except Exception:
        logger.exception(
            "Failed to send BGV status notification for BGV %s",
            bgv_instance.id,
        )


# ── Signals ──────────────────────────────────────────────────────

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
        # ── Fresher: Send BGV link to candidate immediately ─────────────
        logger.info(
            "Fresher candidate %s – sending BGV initiation link to candidate immediately.",
            instance.candidate_name,
        )
        try:
            from .services import send_notification_for_bgv
            send_notification_for_bgv(instance)
        except Exception:
            logger.exception(
                "Failed to auto-send BGV initiation link to candidate for application %s",
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


@receiver(post_save, sender=CandidateBGV)
def sync_bgv_status_to_application(sender, instance, **kwargs):
    """
    Sync CandidateBGV status updates back to the JobApplication and ApprovalNote bgv_status field.
    Also sends email + WhatsApp notifications to assigned HRs.
    """
    app = instance.candidate
    
    status_map = {
        "initiated": "bgv_initiated",
        "in_progress": "bgv_in_progress",
        "completed": "bgv_completed",
        "insufficient": "bgv_insufficient",
    }
    
    new_status = status_map.get(instance.status)
    if not new_status:
        return
        
    if app.bgv_status != new_status:
        app.bgv_status = new_status
        app.save(update_fields=['bgv_status'])
        
        # Also sync to the latest ApprovalNote
        latest_note = ApprovalNote.objects.filter(candidate=app).order_by('-id').first()
        if latest_note and latest_note.bgv_status != new_status:
            latest_note.bgv_status = new_status
            latest_note.save(update_fields=['bgv_status'])
            
        logger.info(
            "Synced BGV status '%s' -> '%s' for application %s",
            instance.status, new_status, app.id
        )

        # ── Notify assigned HRs ──────────────────────────────
        display_status = BGV_STATUS_DISPLAY.get(instance.status, instance.status)
        _notify_hr_bgv_status_change(instance, display_status)