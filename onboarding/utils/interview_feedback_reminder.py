from .sender import send_email,send_text
from booking.models import Booking
from slots.models import InterviewFeedback
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
# REMINDER_INTERVAL = 7200  # 120 minutes


def _get_experience_level(candidate) -> str:
    """Determine fresher/junior/senior based on experience_years (primary)
    or fallback to designation.expirience range. Used to select the
    correct level-specific frontend feedback form (techfresher, hrfresher, etc.).
    """
    if getattr(candidate, "experience_years", None) is not None:
        try:
            years = float(candidate.experience_years)
            if years < 1.5:
                return "fresher"
            elif years < 5.0:
                return "junior"
            else:
                return "senior"
        except (ValueError, TypeError):
            pass

    # Fallback using MRF/Job designation experience range (note spelling in model)
    job = getattr(candidate, "job", None)
    if job and getattr(job, "mrf", None) and getattr(job.mrf, "designation", None):
        exp_str = (job.mrf.designation.expirience or "").lower()
        if any(k in exp_str for k in ["fresher", "fresh", "0-1", "0", "<1"]):
            return "fresher"
        if any(k in exp_str for k in ["junior", "2-4", "1-3", "associate"]):
            return "junior"
        return "senior"

    # Default
    return "junior"


def get_feedback_link(candidate, round_name: str) -> str:
    """Return the correct level-specific feedback form URL for the given round.
    Updated per new frontend routes (/api/slots/techfresher/, /api/slots/hrjunior/,
    /api/slots/techsenior/ etc.). Round is still passed via query param so the form
    knows which questions/fields to show. This replaces the old generic
    *-feedback-form endpoints and fixes link/round mismatch.
    """
    FRONTEND_URL = getattr(settings, "FRONTEND_URL", "https://hirepro.knowcraftanalytics.com")

    level = _get_experience_level(candidate)

    # Map round to base prefix (hr vs tech forms) + query param
    if round_name == "hr_round":
        base = "hr"
        rparam = "hr_round"
    else:
        # All technical/final/management rounds use tech* forms (level determines variant)
        base = "tech"
        rparam = round_name

    endpoint = f"{base}{level}"
    return (
        f"{FRONTEND_URL}/api/slots/{endpoint}/"
        f"?interview_round={rparam}&job_application={candidate.id}"
    )

def send_feedback_reminder_email(interviewer_email, interviewer_name, interviewer_phone, candidate_name, round_name,link,position):
    subject = f"Gentle Reminder: Interview Feedback Form Pending ({round_name})"

    text = f"""
Hi {interviewer_name},

I hope you are doing well.

This is a gentle reminder to kindly complete the Interview Feedback Form for the candidate {candidate_name} you recently interacted with.

The feedback is essential for us to proceed with the next steps in the evaluation process.

Request you to please fill out the form at your earliest convenience.

Please let me know if you require any assistance.

Thank you for your support.

Warm regards,
HR Team
"""
    template = f"""
    <html>
        <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
            <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
                <tr>
                    <td align="center" style="padding:30px 15px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                            <tr>
                                <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                    <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                                </td>
                            </tr>
                            <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                            <tr>
                                <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;line-height:1.5;">
                                    <p style="margin:0 0 16px 0;">Dear {interviewer_name},</p>
                                    <p style="margin:0 0 16px 0;">I hope this message finds you well.</p>
                                    
                                    <p style="margin:0 0 16px 0;">This is a gentle reminder to kindly submit your feedback for the candidate listed below. Your insights are valuable and help us make informed decisions in the recruitment process.</p>
                                    
                                    <p style="margin:0 0 8px 0;font-weight:600;">Candidate Name: {candidate_name}</p>
                                    <p style="margin:0 0 24px 0;font-weight:600;">Position: {position}</p>
                                    
                                    <p style="margin:25px 0 30px 0;text-align:center;">
                                        <a href="{link}" 
                                        style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Complete Feedback Form</a>
                                    </p>
                                    
                                    <p style="margin:0 0 16px 0;">The feedback should take only a few minutes and is critical for moving forward with the evaluation. If you require any assistance or have questions about the form, please feel free to reply to this email.</p>
                                    <br>
                                    <p style="margin:20px 0 6px 0;color:#555555;">Thank you for your time and continued support.</p>
                                    <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                    <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
    </html>"""
    send_email(
        to=interviewer_email,
        subject=subject,
        text=text,
        template=template
    )
    if interviewer_phone:
        send_text(to=interviewer_phone,text=text)
    print("Reminder for feedback sent!")

def interview_feedback_reminder_task(booking_id, round_name=None):
    try:
        booking = Booking.objects.select_related(
            "candidate",
            "interviewer",
            "candidate__job",
            "candidate__job__mrf",
            "candidate__job__mrf__designation",  # for experience level fallback
        ).get(id=booking_id)
    except Booking.DoesNotExist:
        logger.warning(f"Booking {booking_id} does not exist. Skipping reminder.")
        return False

    # Resolve round_name. Use the explicitly passed value (frozen at booking
    # time) so we are immune to candidate-status changes that happen between
    # booking and reminder execution.
    if not round_name:
        status_to_round = {
            "shortlisted": "hr_round",
            "interview_pending_1": "hr_round",
            "interview_done_1": "hr_round",
            "interview_rejected_1": "hr_round",
            "interview_next_2": "technical_round",
            "interview_pending_2": "technical_round",
            "interview_done_2": "technical_round",
            "interview_rejected_2": "technical_round",
            "interview_next_3": "case_study_round",
            "interview_pending_3": "case_study_round",
            "interview_done_3": "case_study_round",
            "interview_rejected_3": "case_study_round",
            "interview_next_final": "final_round",
            "interview_pending_final": "final_round",
            "interview_done_final": "final_round",
            "interview_rejected_final": "final_round",
            "interview_next_management_client": "management_client_round",
            "interview_pending_management_client": "management_client_round",
            "interview_done_management_client": "management_client_round",
            "interview_rejected_management_client": "management_client_round",
        }
        round_name = status_to_round.get(
            booking.candidate.status,
            getattr(booking.candidate, "round_name", None)
        ) or "final_round"

    # ── CHECK 1: Feedback already submitted? ─────────────────────
    # Do this FIRST, before the end-time check.  If feedback is already in,
    # there is zero reason to keep this chain alive — regardless of whether
    # the interview has technically "ended" or not.
    feedback_exists = InterviewFeedback.objects.filter(
        job_application=booking.candidate,
        interview_round=round_name,
    ).exists()

    if feedback_exists:
        logger.info(
            f"Feedback already submitted for Booking {booking.id} "
            f"(round={round_name}). Cancelling further reminders."
        )
        from scheduler.services import TaskScheduler
        TaskScheduler.cancel(
            "interview_feedback_reminder",
            task_kwargs_filter={"booking_id": str(booking_id)},
        )
        return False  # stop the recurring chain

    # ── CHECK 2: Candidate status no longer requires a reminder? ──
    # Only send reminders when the candidate is still at the
    # interview_pending_X status for this round.  Once the status
    # changes to interview_done_X, interview_next_Y,
    # interview_rejected_X, or any later pipeline status, there is
    # no need to keep reminding — the interview outcome has already
    # been recorded or the candidate has moved on.
    ROUND_PENDING_STATUS = {
        "hr_round": {"shortlisted", "interview_pending_1"},
        "technical_round": {"interview_pending_2"},
        "case_study_round": {"interview_pending_3"},
        "final_round": {"interview_pending_final"},
        "management_client_round": {"interview_pending_management_client"},
    }

    candidate_status = booking.candidate.status
    allowed_statuses = ROUND_PENDING_STATUS.get(round_name, set())

    if candidate_status not in allowed_statuses:
        logger.info(
            f"Candidate {booking.candidate.id} status is '{candidate_status}' "
            f"(not pending for round '{round_name}'). Stopping reminder."
        )
        from scheduler.services import TaskScheduler
        TaskScheduler.cancel(
            "interview_feedback_reminder",
            task_kwargs_filter={"booking_id": str(booking_id)},
        )
        return False

    # ── CHECK 3: Interview not over yet? ─────────────────────────
    # If the interview hasn't ended, do NOT send a reminder and do NOT
    # reschedule via the recurring chain.  Return False so the scheduler
    # stops creating follow-up tasks.  The original booking signal already
    # scheduled this task for 30 min after the interview end time; if we
    # got here early (e.g. after a server restart / reconciliation with
    # delay=0), we should NOT keep retrying every 2 hours — that causes
    # premature reminders.  Instead, re-arm a one-shot timer for the
    # correct remaining delay.
    now = timezone.now()
    if booking.end:
        end = booking.end
        if timezone.is_naive(end):
            end = timezone.make_aware(end, timezone.get_current_timezone())
        from datetime import timedelta
        target_time = end + timedelta(minutes=30)  # same 30-min buffer as signal
        if target_time > now:
            remaining = int((target_time - now).total_seconds())
            logger.info(
                f"Interview not over yet for Booking {booking_id} "
                f"(end={end}, now={now}). Re-arming in {remaining}s."
            )
            # Schedule a fresh one-shot task for the correct time instead
            # of blindly re-running in 2 hours.
            from scheduler.services import TaskScheduler
            TaskScheduler.schedule(
                task_type="interview_feedback_reminder",
                task_kwargs={
                    "booking_id": str(booking_id),
                    "round_name": round_name,
                },
                delay_seconds=remaining,
                is_recurring=True,
                interval_seconds=7200,
            )
            return False  # stop THIS chain; the new task takes over

    # ── All clear — send the reminder ────────────────────────────
    link = get_feedback_link(booking.candidate, round_name)

    send_feedback_reminder_email(
        interviewer_email=booking.interviewer.email,
        interviewer_name=booking.interviewer.name,
        interviewer_phone=getattr(booking.interviewer, "phone", None),
        candidate_name=booking.candidate.candidate_name,
        round_name=round_name,
        link=link,
        position=(
            booking.candidate.job.mrf.designation.name
            if booking.candidate.job and booking.candidate.job.mrf and booking.candidate.job.mrf.designation
            else "the position"
        ),
    )
    logger.info(
        f"Reminder email sent for Booking {booking.id} (round={round_name}) "
        f"to {booking.interviewer.email}"
    )

    return True  # continue the recurring reminder chain

    # # Re-enqueue task to run again after 5 minutes
    # def requeue():
    #     TASK_QUEUE.enqueue(interview_feedback_reminder_task, booking_id)

    # import threading
    # threading.Timer(REMINDER_INTERVAL, requeue).start()
    # NOTE: No more threading.Timer re-enqueue here.
    # The TaskScheduler handles recurring re-execution automatically.