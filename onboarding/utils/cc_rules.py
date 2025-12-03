# cc_rules.py
from accounts.models import User

CC_RULES = {
    "shortlisted": ["consultancy","referer"],
    "interview_pending": ["consultancy"],
    "interview_done": ["recruiter"],
    "interview_rejected": [ "consultancy","referer"],

    # "selected": ["hr", "department_head"],
    # "approval_pending": ["approver", "hr"],
    "approved": [ "consultancy"],
    # "approval_rejected": ["hr", "recruiter"],

    # "offer_pending": ["recruiter"],
    "offer_sent": ["consultancy"],
    "offer_accepted": ["consultancy","referer"],
    "offer_rejected": ["consultancy","referer"],
    "resignation_pending": ["consultancy"],
    "salary_docs_pending": ["consultancy"],
    "docs_pending": ["consultancy"],
    # "docs_received": ["hr", "onboarding_team"],
    "docs_approved":["consultancy"],
    "joining_pending": ["consultancy"],
    "joined": ["consultant", "referer","hr_manager"],

    "duplicate_rejected": ["consultancy","referer"],
    "rejected": ["consultancy","referer"],
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

    # mrf = getattr(job, "mrf", None)
    company = getattr(job, "company", None)

    # Helper to add email if exists
    def add(user):
        if user and getattr(user, "email", None):
            emails.add(user.email)

    # Loop role by role
    for role in roles:

        # ---------------------------
        # MRF-based roles
        # ---------------------------
        # if role == "hr":
        #     add(getattr(mrf, "hr", None))

        # elif role == "hr_manager":
        #     add(getattr(mrf, "hr_manager", None))

        # elif role == "recruiter":
        #     add(getattr(mrf,  None))

        # elif role == "interviewer":
        #     # interviewer can be many
        #     interviewer = getattr(mrf, "interviewer", None)
        #     if interviewer:
        #         if hasattr(interviewer, "all"):
        #             for u in interviewer.all():
        #                 add(u)
        #         else:
        #             add(interviewer)

        # elif role == "department_head":
        #     add(getattr(mrf, "department_head", None))

        # ---------------------------
        # Company roles → User table
        # ---------------------------
        # elif role in ["admin", "internal_team", "consultancy"]:
        #     if company and hasattr(company, "users"):
        #         qs = company.users.filter(role=role)
        #         for user in qs:
        #             add(user)

        # ---------------------------
        # Referral-based roles
        # ---------------------------
        # elif role == "referrer":
        #     if getattr(candidate, "referer", None):
        #         emails.add(candidate.referral_email)

        # ---------------------------
        # Consultant for consultancy agencies
        # ---------------------------
        # elif role == "consultant":
        #     if getattr(candidate, "consultant_email", None):
        #         emails.add(candidate.consultant_email)
        role_emails = list(
                company.users.filter(role=role)
                .exclude(email__isnull=True)
                .exclude(email="")
                .values_list("email", flat=True)
            )
        for e in role_emails:
                emails.add(e)
    return list(emails)

def get_cc_for_stage(candidate, stage):
    base_cc = CC_RULES.get(stage, [])

    # Add referral CC only if candidate has referrer
    # if candidate.referral_email:
    #     base_cc.append("referral")

    # Convert role names → actual email list
    return get_emails_for_role(candidate,base_cc)
