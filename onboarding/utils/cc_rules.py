# cc_rules.py
from accounts.models import User

CC_RULES = {
    "shortlisted": ["consultancy","referrer"],
    "interview_pending_1": ["consultancy","interviewer_1"],
    "interview_done_1": [],
    "interview_rejected_1": [ "consultancy","referrer"],
    "interview_next_2": ["consultancy","referrer"],
    "interview_pending_2": ["consultancy","interviewer_2"],
    "interview_done_2": [],
    "interview_rejected_2": [ "consultancy","referrer"],
    "interview_next_3": ["consultancy","referrer"],
    "interview_pending_3": ["consultancy","interviewer_2"],
    "interview_done_3": [],
    "interview_rejected_3": [ "consultancy","referrer"],
    "interview_next_final": ["consultancy","referrer"],
    "interview_pending_final": ["consultancy","interviewer_final"],
    "interview_done_final": [],
    "interview_rejected_final": [ "consultancy","referrer"],
    "interview_next_management_client": ["consultancy", "referrer"],
    "interview_pending_management_client": ["consultancy", "interviewer_management_client"],
    "interview_done_management_client": [],
    "interview_rejected_management_client": ["consultancy", "referrer"],
    # "selected": ["hr", "department_head"],
    # "approval_pending": ["approver", "hr"],
    "approved": [ "consultancy"],
    # "approval_rejected": ["hr", "recruiter"],

    # "offer_pending": ["recruiter"],
    "offer_sent": ["consultancy"],
    "offer_accepted": ["consultancy","referrer"],
    "offer_rejected": ["consultancy","referrer"],
    "resignation_pending": ["consultancy"],
    "salary_docs_pending": ["consultancy"],
    "docs_pending": ["consultancy"],
    # "docs_received": ["hr", "onboarding_team"],
    "docs_approved":["consultancy"],
    "joining_pending": ["consultancy"],
    "joined": ["consultant", "referrer","hr_manager"],

    "duplicate_rejected": ["consultancy","referrer"],
    "rejected": ["consultancy","referrer"],
}

def get_emails_for_role(candidate, roles):
    """
    roles may be a single string or list of role names.
    Returns a flat list of unique emails.
    """

    if isinstance(roles, str):
        roles = [roles]

    emails = set()

    job = getattr(candidate, "job", None)
    if not job:
        return []

    mrf = getattr(job, "mrf", None)
    company = getattr(job, "company", None)

    # Helper
    def add_email(email):
        if email:
            emails.add(email)

    def add_user(user):
        if user and getattr(user, "email", None):
            emails.add(user.email)

    def add_users(qs):
        for user in qs:
            add_user(user)

    # Loop role by role
    for role in roles:

        # =========================
        # CONSULTANCY (FIXED)
        # =========================
        if role == "consultancy":
            if candidate.source == "consultancy":
                # OLD (single)
                add_user(getattr(job, "assigned_to_consultancy", None))

                # NEW (multiple)
                if hasattr(job, "assigned_consultancies"):
                    add_users(job.assigned_consultancies.all())

        # =========================
        # INTERNAL HR (STRICT ASSIGNED ONLY)
        # =========================
        elif role == "hr":
            # OLD (single)
            add_user(getattr(job, "assigned_to_internal_hr", None))

            # NEW (multiple)
            if hasattr(job, "assigned_internal_hrs"):
                add_users(job.assigned_internal_hrs.all())

        # =========================
        # REFERRER (CANDIDATE BASED)
        # =========================
        elif role == "referrer":
            if getattr(candidate, "referral_email", None):
                add_email(candidate.referral_email)

        # =========================
        # INTERVIEWERS (SAFE)
        # =========================
        elif role == "interviewer_1":
            if mrf:
                add_email(getattr(mrf, "interviewer_email_1", None))

        elif role == "interviewer_2":
            if mrf and hasattr(mrf, "technical_interviewers"):
                add_users(mrf.technical_interviewers.all())

        elif role == "interviewer_3":
            if mrf:
                add_email(getattr(mrf, "interviewer_email_3", None))

        elif role == "interviewer_final":
            if mrf:
                add_email(getattr(mrf, "interviewer_email_final", None))

        elif role == "interviewer_management_client":
            if mrf:
                add_email(getattr(mrf, "interviewer_email_management_client", None))

        # =========================
        # COMPANY ROLE FALLBACK (RESTORED)
        # =========================
        elif role in ["admin", "hr_manager"]:
            if company and hasattr(company, "users"):
                users = company.users.filter(
                    role=role
                ).exclude(email__isnull=True).exclude(email="")

                add_users(users)

    return list(emails)

def get_cc_for_stage(candidate, stage):
    base_cc = CC_RULES.get(stage, [])

    # Add referral CC only if candidate has referrer
    # if candidate.referral_email:
    #     base_cc.append("referral")

    # Convert role names → actual email list
    return get_emails_for_role(candidate,base_cc)
