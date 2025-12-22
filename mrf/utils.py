# # mrf/utils.py
# from datetime import time
# from django.utils import timezone
# from .models import MRF

# def is_after_5pm(dt):
#     dt_local = dt.astimezone(timezone.get_default_timezone())
#     return dt_local.time() > time(17, 0, 0)

# def determine_next_working_date_if_after_5pm(dt):
#     # returns date
#     if is_after_5pm(dt):
#         from .models import next_working_day
#         return next_working_day(dt)
#     return dt.astimezone(timezone.get_default_timezone()).date()

SALARY_BANDS = {
    "Valuation": {
        "Analyst": (500000, 700000),
        "Advanced Analysts": (700000, 950000),
        "Senior Analysts-I": (950000, 1250000),
        "Senior Analysts-II": (1250000, 1550000),
        "Assistant Managers": (1550000, 2200000),
        "Associate Manager": (2200000, 2700000),
        "Manager": (2500000, 3000000),
        "Senior Manager": (3000000, 4000000),
    },

    "Investment Banking": {
        "Analyst": (500000, 650000),
        "Adv. Analysts": (650000, 850000),
        "Senior Analysts-I": (850000, 1150000),
        "Senior Analysts-II": (1150000, 1450000),
        "Assistant Managers": (1450000, 2000000),
        "Associate Manager": (2200000, 2700000),
        "Manager": (2500000, 3000000),
        "Senior Manager": (2500000, 3200000),
    },

    "US Accounts": {
        "Associate": (400000, 550000),
        "Advanced Associates": (500000, 650000),
        "Senior Associates I": (650000, 800000),
        "Senior Associates-II": (800000, 1000000),
        "Team Lead": (1000000, 1300000),
        "Assistant Manager": (1300000, 1500000),
        "Associate Manager": (1500000, 1750000),
        "Manager": (1750000, 2250000),
    },

    "US Tax": {
        "Associate": (400000, 500000),
        "Advanced Associates": (500000, 650000),
        "Senior Associates I": (650000, 800000),
        "Senior Associates-II": (800000, 1000000),
        "Team Lead": (1000000, 1300000),
        "Assistant Manager": (1300000, 1750000),
        "Associate Manager": (1500000, 1750000),
        "Manager": (1750000, 2250000),
    },

    "FDD": {
        "Associate": (400000, 500000),
        "Advanced Associates": (500000, 650000),
        "Senior Associates I": (650000, 800000),
        "Senior Associates-II": (800000, 1000000),
        "Team Lead": (1000000, 1300000),
        "Assistant Manager": (1300000, 1500000),
        "Associate Manager": (1500000, 1750000),
        "Manager": (1750000, 2250000),
    },

    "Marketing": {
        "Associate": (300000, 450000),
        "Advanced Associates": (400000, 500000),
        "Senior Associates": (500000, 650000),
        "Team Lead": (600000, 800000),
        "Assistant Manager": (800000, 1000000),
        "Associate Manager": (1000000, 1300000),
        "Manager": (1200000, 1500000),
    },

    "HR and Administration": {
        "Associate": (300000, 450000),
        "Advanced Associates": (400000, 500000),
        "Senior Associates": (500000, 650000),
        "Team Lead": (600000, 800000),
        "Assistant Manager": (800000, 1000000),
        "Associate Manager": (1000000, 1300000),
        "Manager": (1200000, 1500000),
    },

    "Information Technology": {
        "Associate": (300000, 450000),
        "Advanced Associates": (400000, 500000),
        "Senior Associates": (500000, 650000),
        "Team Lead": (600000, 800000),
        "Assistant Manager": (800000, 1000000),
        "Associate Manager": (1000000, 1300000),
        "Manager": (1200000, 1500000),
    },

    "Internal Accounts": {
        "Associate": (300000, 450000),
        "Advanced Associates": (400000, 500000),
        "Senior Associates": (500000, 650000),
        "Team Lead": (600000, 800000),
        "Assistant Manager": (800000, 1000000),
        "Associate Manager": (1000000, 1300000),
        "Manager": (1200000, 1500000),
    },
}
from django.core.exceptions import ValidationError

def validate_salary_range(salary_range,department_name,designation_name):
    if hasattr(department_name, "name"):
        department_name = department_name.name

    if hasattr(designation_name, "name"):
        designation_name = designation_name.name

    if department_name not in list(SALARY_BANDS.keys()):
            return

    if designation_name not in list(SALARY_BANDS[department_name].keys()):
        return

    allowed_min, allowed_max = SALARY_BANDS[department_name][designation_name]
        # Parse salary_range (e.g. "5-8 LPA" → 500000 - 800000)
    try:
        parts = salary_range.lower().replace("lpa", "").replace(",", "").replace("to", "-").replace(",", "").replace(" ", "").strip()
        if "-" not in parts:
            raise ValueError("Salary range must contain '-'")
        raw_min,raw_max = parts.split('-')
        s_min,s_max = float(raw_min),float(raw_max)
        if s_min < 1000:
            s_min = s_min * 100000
        if s_max < 1000:
            s_max = s_max * 100000
    except Exception:
        raise ValidationError("Salary must be in valid range format.")

    # Validate boundaries
    if s_min < allowed_min or s_max > allowed_max:
        raise ValidationError(
            f"Salary for {designation_name} in {department_name} must be between "
            f"{allowed_min:,} and {allowed_max:,}."
        )

def get_auto_salary_range(department, designation):
    # Handle model instances
    if hasattr(department, "name"):
        department = department.name

    if hasattr(designation, "name"):
        designation = designation.name

    department = str(department).strip()
    designation = str(designation).strip()
    try:
        if department not in list(SALARY_BANDS.keys()):
            return

        if designation not in list(SALARY_BANDS[department].keys()):
            return

        min_sal, max_sal = SALARY_BANDS[department][designation]
        return f"{min_sal} - {max_sal}"
    except KeyError:
        return None

email_templates = {
    "mrf_submit_new":f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <p>Dear <strong>{{manager_name}}</strong>,</p>
        <p>
            We would like to inform you that a requisition for
            <strong>{{designation}}</strong> position was raised by 
            <strong>{{hod_name}}</strong> on <strong>{{date}}</strong> 
            as a <strong>new request</strong>.
        </p>
        <p>
            We kindly request you to review the requisition and take the necessary 
            action at the earliest.
        </p>
        <p>Thank you for your support.</p>
        <p>
            Best regards,<br>
            <strong>Team HR</strong>
        </p>
    </body>
    </html>""",
    "mrf_submit_replace":f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <p>Dear <strong>{{manager_name}}</strong>,</p>
        <p>
            We would like to inform you that a requisition for 
            <strong>{{designation}}</strong> position was raised by 
            <strong>{{hod_name}}</strong> on <strong>{{date}}</strong>, 
            for the replacement of <strong>{{resigned_employee}}</strong>.
        </p>
        <p>
            We kindly request you to review the requisition and take the necessary 
            action at the earliest.
        </p>
        <p>Thank you for your support.</p>
        <p>
            Best regards,<br>
            <strong>Team HR</strong>
        </p>
    </body>
    </html>
    """,
    "mrf_reminder":f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
        <p>Dear {{manager_name}},</p>
        <p>
            This is a gentle reminder that a requisition for an 
            <strong>{{position}}</strong> position was raised on 
            <strong>{{requisition_date}}</strong>.
        </p>
        <p>
            We kindly request you to review the requisition and take the necessary action at the earliest.
        </p>
        <p>Thank you for your attention.</p>
        <p>Best regards,<br>
        <strong>Team HR</strong></p>
    </body>
    </html>
    """
}

alt_text = {
    "mrf_submit_replace":f"""
Dear {{manager_name}},
We would like to inform you that a requisition for an Analyst – {{designation}} position was raised by {{hod_name}} on {{date}}, for the replacement of {{resigned_employee}}.
We kindly request you to review the requisition and take the necessary action at the earliest.
Thank you for your support.
Best regards,
Team HR
""",
    "mrf_submit_new":f"""Dear {{manager_name}},
We would like to inform you that a requisition for an Analyst – {{designation}} position was raised by {{hod_name}} on {{date}} as a new request.
We kindly request you to review the requisition and take the necessary action at the earliest.
Thank you for your support.
Best regards,
Team HR
""",
    "mrf_reminder":f"""Dear {{manager_name}},
This is a gentle reminder that a requisition for an {{position}} position was raised on {{requisition_date}}.
Kindly review the requisition and take the necessary action at the earliest.
Thank you.
Best regards,
Team HR
"""
}

import threading
import time
from .models import MRF
from accounts.models import User
from onboarding.utils.sender import send_email
def schedule_mrf_reminder(mrf_id):
    """Runs a reminder check after 48 hours in a background thread."""

    def task():
        time.sleep(48 * 60 * 60)  # 48 hours

        try:
            mrf = MRF.objects.get(id=mrf_id)

            # Only send reminder if still pending
            if mrf.status not in ["approved", "rejected"]:
                manager = User.objects.filter(role="hr_manager").first()

                if manager:
                    template = email_templates["mrf_reminder"].format(
                        manager_name=manager.name,
                        position=mrf.designation.name,
                        requisition_date=mrf.created_at.strftime("%B %d, %Y")
                    )

                    text = alt_text["mrf_reminder"].format(
                        manager_name=manager.name,
                        position=mrf.designation.name,
                        requisition_date=mrf.created_at.strftime("%B %d, %Y")
                    )

                    send_email(
                        to=manager.email,
                        subject=f"Reminder – Requisition Pending Review",
                        template=template,
                        text=text
                    )
                    print(f"Reminder email sent for MRF {mrf_id}")

        except Exception as e:
            print(f"Reminder scheduler error: {e}")

    threading.Thread(target=task, daemon=True).start()

from datetime import timedelta
from django.utils import timezone

def get_expected_date_of_joining(designation):
    """
    Calculate expected DOJ based on department-designation TAT model
    """
    from .models import Designation
    if hasattr(designation, "id"):
        designation = designation.id
    tat_days = None
    joining_obj = Designation.objects.filter(id=designation).first()
    if joining_obj and joining_obj.tat_days:
        tat_days = joining_obj.tat_days
    else:
        tat_days= 0

    return timezone.now().date() + timedelta(days=tat_days)