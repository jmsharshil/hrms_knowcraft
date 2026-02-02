from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import InterviewFeedback
from jobs.models import JobApplication


@receiver([post_save, post_delete], sender=InterviewFeedback)
def update_consolidated_feedback_avg(sender, instance, **kwargs):
    application = instance.job_application

    feedbacks = application.interview_feedbacks.all()

    scores = []

    for feedback in feedbacks:
        avg = feedback.get_round_avg()
        if avg is not None:
            scores.append(avg)

    consolidated_avg = round(sum(scores) / len(scores), 2) if scores else 0
    JobApplication.objects.filter(id=application.id).update(
        consolidated_feedback_avg=consolidated_avg
    )
