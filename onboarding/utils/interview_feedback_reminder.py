from .sender import send_email,send_text
from booking.models import Booking
from slots.models import InterviewFeedback
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
# REMINDER_INTERVAL = 7200  # 120 minutes

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

def interview_feedback_reminder_task(booking_id):
    try:
        booking = Booking.objects.select_related("candidate", "interviewer").get(id=booking_id)
    except Booking.DoesNotExist:
        logger.warning(f"Booking {booking_id} does not exist. Skipping reminder.")
        return

    # If interview is not over yet, just return — the recurring scheduler
    # will call us again at the next interval.
    if booking.end > timezone.now():
        # delay = (booking.end - timezone.now()).total_seconds()
        # logger.info(f"Interview not over yet. Will retry after {delay} seconds.")

        # import threading
        # threading.Timer(delay, lambda: TASK_QUEUE.enqueue(
        #     interview_feedback_reminder_task, booking_id
        # )).start()

        logger.info(f"Interview not over yet for Booking {booking_id}. Will retry on next cycle.")
        return

    # Determine interview round from booking status (adjust according to your logic)
    status_to_round = {
        "interview_pending_1": "hr_round",
        "interview_pending_2": "technical_round",
        "interview_pending_3": "cas_study_round",
        "interview_pending_final": "final_round",
        "interview_pending_management_client": "management_client_round",
    }
    round_name = status_to_round.get(booking.candidate.status, "Interview")
    # Check if feedback exists for this candidate, interviewer, date
    feedback_exists = InterviewFeedback.objects.filter(
        job_application=booking.candidate,
        interviewer_name=booking.interviewer.name,
        interview_date=booking.start.date()
    ).exists()

    if feedback_exists or round_name == 'Interview':
        logger.info(f"Feedback already submitted for Booking {booking.id}. No reminder sent.")
        # Cancel further recurring reminders for this booking
        from scheduler.services import TaskScheduler
        TaskScheduler.cancel(
            "interview_feedback_reminder",
            task_kwargs_filter={"booking_id": str(booking_id)},
        )
        return

    # Send reminder email
    send_feedback_reminder_email(
        interviewer_email=booking.interviewer.email,
        interviewer_name=booking.interviewer.name,
        interviewer_phone=booking.interviewer.phone,
        candidate_name=booking.candidate.candidate_name,
        round_name=round_name,
        link= booking.candidate.feedback_link,
        position = booking.candidate.job.mrf.designation.name
    )
    logger.info(f"Reminder email sent for Booking {booking.id} to {booking.interviewer.email}")

    # # Re-enqueue task to run again after 5 minutes
    # def requeue():
    #     TASK_QUEUE.enqueue(interview_feedback_reminder_task, booking_id)

    # import threading
    # threading.Timer(REMINDER_INTERVAL, requeue).start()
    # NOTE: No more threading.Timer re-enqueue here.
    # The TaskScheduler handles recurring re-execution automatically.