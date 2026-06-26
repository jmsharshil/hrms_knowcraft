from .sender import send_email,send_text
from mrf.models import MRF
from django.utils import timezone
import logging
from django.conf import settings

FRONTEND_URL = getattr(settings,"FRONTEND_URL")
logger = logging.getLogger(__name__)
# REMINDER_INTERVAL = 7200  # 120 minutes

def send_mrf_reminder_email(creator_email, creator_name, creator_phone, mrf_name, designation):

    subject = f"Reminder: Please Submit MRF {mrf_name} for Approval"

    text = f"""
Hi {creator_name},

This is a gentle reminder to submit the MRF for the position "{designation}" for approval.

Kindly complete the approval submission so the recruitment process can proceed.

MRF : {mrf_name}

You can submit it using the link below:
{FRONTEND_URL}

Thank you.

HR Team
"""

    template = f"""
<html>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial;">
<table align="center" width="100%" style="max-width:620px;background:#ffffff;border-radius:10px;">
<tr>
<td style="padding:40px;text-align:center;">
<img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:250px;">
</td>
</tr>

<tr>
<td style="padding:30px 40px;color:#333;font-size:16px;line-height:1.6">

<p>Dear {creator_name},</p>

<p>This is a friendly reminder to submit the <b>MRF</b> below for approval.</p>

<p style="margin-top:20px;font-weight:600;">MRF: {mrf_name}</p>
<p style="margin-bottom:20px;font-weight:600;">Position: {designation}</p>

<p style="text-align:center;margin:30px 0;">
<a href="{FRONTEND_URL}" 
style="background:#2563eb;color:#fff;padding:14px 28px;border-radius:6px;text-decoration:none;font-weight:600;">
Submit for Approval
</a>
</p>

<p>Please submit the MRF so that the hiring process can move forward.</p>

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

    send_email(
        to=creator_email,
        subject=subject,
        text=text,
        template=template
    )

    if creator_phone:
        send_text(to=creator_phone, text=text)

    print("MRF reminder sent!")

def mrf_approval_reminder_task(mrf_id):

    try:
        mrf = MRF.objects.select_related("requested_by", "designation").get(id=mrf_id)
    except MRF.DoesNotExist:
        logger.warning(f"MRF {mrf_id} does not exist. Cancelling recurring task.")
        return False
    except Exception as e:
        logger.error(f"Error in mrf_approval_reminder_task for {mrf_id}: {e}")
        return False

    # Check if MRF already sent for approval (or status advanced). Cancel recurring task.
    if mrf.status != "draft":
        logger.info(f"MRF {mrf_id} status={mrf.status} — cancelling recurring reminder.")
        from scheduler.services import TaskScheduler
        TaskScheduler.cancel(
            "mrf_approval_reminder",
            task_kwargs_filter={"mrf_id": str(mrf_id)},
        )
        return False  # stop recurring

    creator = mrf.requested_by

    send_mrf_reminder_email(
        creator_email=creator.email,
        creator_name=creator.name,
        creator_phone=getattr(creator, "phone", None),
        mrf_name=mrf.mrf_name,
        designation=mrf.designation.name,
    )

    logger.info(f"Reminder sent to MRF creator for MRF {mrf_id}")
    return True  # continue recurring
