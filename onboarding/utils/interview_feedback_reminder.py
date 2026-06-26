from .sender import send_email,send_text
from booking.models import Booking
from slots.models import InterviewFeedback
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
# REMINDER_INTERVAL = 7200  # 120 minutes


def get_feedback_link(candidate, round_name: str) -> str:
    """Return the correct feedback form URL for the given round.
    Uses round-specific endpoints so that reminders for earlier rounds
    do not incorrectly pick up the final-round link stored on the candidate.
    """
    FRONTEND_URL = getattr(settings, "FRONTEND_URL", "https://hirepro.knowcraftanalytics.com")
    mapping = {
        "hr_round": ("hr-feedback-form", "hr_round"),
        "technical_round": ("technical-feedback-form-one", "technical_round"),
        "case_study_round": ("technical-feedback-form-two", "case_study_round"),
        "final_round": ("final-feedback-form", "final_round"),
        "management_client_round": ("management-feedback-form", "management_client_round"),
    }
    if round_name in mapping:
        endpoint, rparam = mapping[round_name]
        return (
            f"{FRONTEND_URL}/api/slots/{endpoint}/"
            f"?interview_round={rparam}&job_application={candidate.id}"
        )
    # fallback
    return getattr(candidate, "feedback_link", "") or f"{FRONTEND_URL}/candidate/feedback/{candidate.id}"

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
            "candidate", "interviewer", "candidate__job", "candidate__job__mrf"
        ).get(id=booking_id)
    except Booking.DoesNotExist:
        logger.warning(f"Booking {booking_id} does not exist. Skipping reminder.")
        return False

    # If interview is not over yet, just return — the recurring scheduler
    # will call us again at the next interval.
    if booking.end > timezone.now():
        logger.info(f"Interview not over yet for Booking {booking_id}. Will retry on next cycle.")
        return True  # keep the recurring chain alive

    # Expanded mapping covers pending, done, rejected, and transition states.
    # This ensures the correct round is used even if the candidate status has
    # advanced by the time a recurring reminder fires.
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
    computed_round = status_to_round.get(
        booking.candidate.status,
        getattr(booking.candidate, "round_name", None)
    )
    round_name = round_name or computed_round or "final_round"

    # Use interview_round for lookup — matches exactly what the feedback form
    # and serializer use. This fixes the "feedback_exists never true" bug
    # caused by interviewer_name / date mismatches (e.g. HR round name).
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
        return False  # tell scheduler not to create the next recurring task

    # Build link based on *this* round (not the possibly-updated
    # candidate.feedback_link which reflects the latest round).
    link = get_feedback_link(booking.candidate, round_name)

    # Send reminder
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
    # NOTE: Scheduler._execute now checks the return value and stops rescheduling
    # when False is returned. Combined with the per-round check this fully resolves
    # "reminders continue after feedback submitted" and the wrong-round/wrong-link bugs.

    # # Re-enqueue task to run again after 5 minutes
    # def requeue():
    #     TASK_QUEUE.enqueue(interview_feedback_reminder_task, booking_id)

    # import threading
    # threading.Timer(REMINDER_INTERVAL, requeue).start()
    # NOTE: No more threading.Timer re-enqueue here.
    # The TaskScheduler handles recurring re-execution automatically.