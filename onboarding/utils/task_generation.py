# onboarding/utils/task_generation.py

from datetime import timedelta
from django.utils import timezone
from onboarding.models import OnboardingTaskList, OnboardingTask
from onboarding.utils.notifications import send_email


def get_or_create_task_list(app):
    task_list, _ = OnboardingTaskList.objects.get_or_create(
        job_application=app,
        defaults={"name": f"Onboarding — {app.candidate_name}"},
    )
    return task_list


def create_task(app, title, description="", due_date=None, assigned_to=None, team=None):
    """
    Idempotent per (task_list, title) — daily check can call this every day for the
    same milestone without creating duplicates.
    """
    task_list = get_or_create_task_list(app)
    task, created = OnboardingTask.objects.get_or_create(
        task_list=task_list,
        title=title,
        defaults={
            "description": description,
            "due_date": due_date,
            "assigned_to": assigned_to,
        },
    )
    if created and team:
        email_to = None
        if team == "it":
            email_to = "itsupport@knowcraft.in"
        elif team in ["hr", "admin"]:
            if app.job and app.job.assigned_to_internal_hr:
                email_to = app.job.assigned_to_internal_hr.email
        
        if email_to:
            subject = f"New Onboarding Task: {title}"
            body = f"A new onboarding task has been created for candidate {app.candidate_name}.\n\nTask: {title}\nDue Date: {due_date}"
            # Assuming send_email takes recipient, subject, text as arguments. 
            send_email(email_to, subject=subject, text=body, event="onboarding_task_created", email_type="internal")
            
    return task, created


def create_milestone_tasks(app, milestone_key, joining_date):
    """
    Central place mapping each diagram milestone -> concrete OnboardingTask rows,
    branched by joining_type / hotel_required / bond_required.
    Called from daily_onboarding_check at the matching days_until_joining branch.
    """
    is_office = app.job.job_type == "work_from_office"

    if milestone_key == "DOJ_MINUS_15":
        create_task(app, "Procure laptop", due_date=joining_date - timedelta(days=10), team="it")
        if not is_office:
            create_task(app, "VPN setup (remote joiner)", due_date=joining_date - timedelta(days=10), team="it")

    elif milestone_key == "DOJ_MINUS_7":
        if is_office:
            create_task(app, "Notify HOD of office joining", due_date=joining_date - timedelta(days=6), team="hr")
            create_task(app, "Prepare ID card / desk / access card", due_date=joining_date - timedelta(days=1), team="admin")
        else:
            create_task(app, "Confirm laptop dispatch (remote joiner)", due_date=joining_date - timedelta(days=1), team="admin")

    elif milestone_key == "DOJ_0_DOCS":
        create_task(app, "Generate statutory documents", due_date=joining_date, team="hr")
        create_task(app, "Send documents for e-signature via Flowace", due_date=joining_date, team="hr")
        if getattr(app, "bond_required", False):
            create_task(app, "Include Employment Bond in esign packet", due_date=joining_date, team="hr")

    elif milestone_key == "DOJ_PLUS_1_ESIGN_REMINDER":
        create_task(app, "Check for unsigned esign documents", due_date=joining_date + timedelta(days=1), team="hr")

    elif milestone_key == "DOJ_PLUS_7_BGV":
        create_task(app, "Re-check BGV status", due_date=joining_date + timedelta(days=7), team="hr")

    elif milestone_key == "DOJ_PLUS_30_SURVEY":
        create_task(app, "Send Day 30 satisfaction survey", due_date=joining_date + timedelta(days=30), team="hr")

    elif milestone_key == "DOJ_PLUS_45_CHECKIN":
        create_task(app, "Schedule Day 45 check-in call", due_date=joining_date + timedelta(days=45), team="hr")

    elif milestone_key == "DOJ_PLUS_90_FINAL":
        create_task(app, "Schedule Day 90 final review", due_date=joining_date + timedelta(days=90), team="hr")
        create_task(app, "Close IT ManageEngine ticket", due_date=joining_date + timedelta(days=90), team="it")