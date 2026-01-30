from .sender import send_email
from .task_queue import TASK_QUEUE
from booking.models import Booking
from slots.models import InterviewFeedback
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
REMINDER_INTERVAL = 7200  # 5 minutes

def send_feedback_reminder_email(interviewer_email, interviewer_name, candidate_name, round_name):
    subject = f"Reminder: Interview Feedback Pending ({round_name})"

    text = f"""
Hi {interviewer_name},

This is a reminder to submit your interview feedback.

Candidate: {candidate_name}
Interview Round: {round_name}

Please submit the feedback at the earliest.

Thank you,
HR Team
"""
    send_email(
        to=interviewer_email,
        subject=subject,
        text=text
    )
    print("Reminder for feedback sent!")

def interview_feedback_reminder_task(booking_id):
    try:
        booking = Booking.objects.select_related("candidate", "interviewer").get(id=booking_id)
    except Booking.DoesNotExist:
        logger.warning(f"Booking {booking_id} does not exist. Skipping reminder.")
        return

    # Only send reminder if interview is over
    if booking.end > timezone.now():
        delay = (booking.end - timezone.now()).total_seconds()
        logger.info(f"Interview not over yet. Will retry after {delay} seconds.")

        import threading
        threading.Timer(delay, lambda: TASK_QUEUE.enqueue(
            interview_feedback_reminder_task, booking_id
        )).start()
        return

    # Determine interview round from booking status (adjust according to your logic)
    status_to_round = {
        "interview_pending_1": "hr_round",
        "interview_pending_2": "technical_round_1",
        "interview_pending_3": "technical_round_2",
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

    if feedback_exists:
        logger.info(f"Feedback already submitted for Booking {booking.id}. No reminder sent.")
        return

    # Send reminder email
    send_feedback_reminder_email(
        interviewer_email=booking.interviewer.email,
        interviewer_name=booking.interviewer.name,
        candidate_name=booking.candidate.candidate_name,
        round_name=round_name
    )
    logger.info(f"Reminder email sent for Booking {booking.id} to {booking.interviewer.email}")

    # Re-enqueue task to run again after 5 minutes
    def requeue():
        print("Again.............Untill you die!")
        TASK_QUEUE.enqueue(interview_feedback_reminder_task, booking_id)

    import threading
    threading.Timer(REMINDER_INTERVAL, requeue).start()