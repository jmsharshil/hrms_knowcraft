# cc_rules.py
from accounts.models import User

CC_RULES = {
    "shortlisted": ["recruiter", "hr"],
    "interview_pending": ["recruiter", "hr"],
    "interview_done": ["recruiter", "hr"],
    "interview_rejected": ["recruiter", "hr"],

    "selected": ["hr", "department_head"],
    "approval_pending": ["approver", "hr"],
    "approved": ["hr", "recruiter", "finance"],
    "approval_rejected": ["hr", "recruiter"],

    "offer_pending": ["hr", "recruiter"],
    "offer_sent": ["hr"],
    "offer_accepted": ["hr", "recruiter", "finance"],
    "offer_rejected": ["hr"],

    "docs_pending": ["hr", "onboarding_team"],
    "docs_received": ["hr", "onboarding_team"],

    "joining_pending": ["hr", "onboarding_team", "it", "finance"],
    "joined": ["hr", "finance", "it", "consultant", "referral"],

    "duplicate_rejected": ["recruiter"],
    "rejected": ["recruiter", "hr"],
}
def get_emails_for_role(candidate, role):
    #put logic here
    return []

def get_cc_for_stage(candidate, stage):
    base_cc = CC_RULES.get(stage, [])

    # Add referral CC only if candidate has referrer
    if candidate.referral_email:
        base_cc.append("referral")

    # Convert role names → actual email list
    return get_emails_for_role(candidate,base_cc)
