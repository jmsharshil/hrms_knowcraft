# engine.py
import logging
from .stage_transition_rules import get_auto_next, validate_transition
from .notifications import notify_candidate,notify_internal
from .cc_rules import get_cc_for_stage
logger = logging.getLogger(__name__)


# ------------------------------
# Notification rules for ALL STATES
# ------------------------------
NOTIFY_STATES = {
    # Screening & Interview
    "shortlisted",
    "interview_pending_1",
    "interview_done_1",
    "interview_rejected_1",
    "interview_next_2",
    "interview_pending_2",
    "interview_done_2",
    "interview_rejected_2",
    "interview_next_final",
    "interview_pending_final",
    "interview_done_final",
    "interview_rejected_final",
    # Approval
    "approved",
    # "approval_rejected",
    # Salary Docs
    "salary_docs_pending",
    # "salary_docs_uploaded",
    # "hr_review_docs",
    # "hr_review_ok",
    "hr_review_rejected",
    # Salary Annexure
    # "salary_annexure_prep",
    # "salary_annexure_sent",
    # "approved_annexure",
    # "rejected_annexure",
    # Offer
    # "offer_pending",
    "offer_sent",
    "offer_accepted",
    "offer_rejected",
    # Resignation
    "resignation_pending",
    # "resignation_uploaded",
    # "resignation_review",
    # "resignation_approved",
    "resignation_rejected",
    # Documents
    "docs_pending",
    # "docs_uploaded",
    # "review_docs",
    "docs_approved",
    "docs_incomplete",
    "docs_unclear",
    # Joining
    "joining_pending",
    # "joining_poned",
    "joined",
    # Final rejections
    "duplicate_rejected",
    "rejected",
}

NOTIFY_INTERNAL_STATES = {
    # Approval Flow
    "approval_pending",        # Send approval request to HR Manager
    "approved",                # Notify HR
    "approval_rejected",       # Notify HR
    # Salary Documents Flow
    "salary_docs_uploaded",    # Notify HR for review
    # Salary Annexure Flow
    "salary_annexure_prep",    # Notify HR to prepare annexure
    "salary_annexure_sent",    # Notify HR manager
    "approved_annexure",       # Notify HR
    "rejected_annexure",       # Notify HR
    # Offer Flow (Internal Steps)
    "offer_pending",           # Notify HR to prepare offer
    "offer_rejected",
    # Resignation Collection
    "resignation_uploaded",    # HR reviews
    # Document Verification
    "docs_uploaded",           # HR reviews
    # Joining
    "joining_pending",         # Notify HR/IT/Admin internally
    "joining_poned",           # Internal delay notice
    "joined",                  # Broadcast to departments
    # Duplicate or general rejection internal notices
    "duplicate_rejected",
    "rejected",
}

# ------------------------------
# Broadcast rules for internal teams
# ------------------------------
BROADCAST_ON_JOIN = True


def automation_engine(candidate, old, new):
    logger.info(f"AUTO: {candidate.candidate_name} {old} → {new}")

    # 1️⃣ Validate transition
    ok, reason = validate_transition(old, new)
    if not ok:
        logger.error(f"❌ Invalid transition: {old} → {new}. Reason: {reason}")
        return False,reason

    # 2️⃣ Send candidate notifications (if applicable)
    if new in NOTIFY_STATES:
        try:
            cc = get_cc_for_stage(candidate,new)
            notify_candidate(candidate, new,cc=cc or [])
            logger.info(f"AUTO: Notification sent for {candidate.candidate_name} → {new}")
        except Exception as e:
            logger.exception(f"❌ Error sending notification: {e}")

    # 3️⃣ Send internal person notifications (if applicable)        
    if new in NOTIFY_INTERNAL_STATES:
        try:
            notify_internal(candidate, new, cc=[])
            logger.info(f"AUTO: Internal Notification sent for {candidate.candidate_name} → {new}")
        except Exception as e:
            logger.exception(f"❌ Internal Notification Error: {e}")
    # # 3️⃣ Internal broadcasting for key events
    # if new == "joined" and BROADCAST_ON_JOIN:
    #     logger.info(
    #         f"AUTO: Broadcasting joining of {candidate.candidate_name} to Head/HR/Finance/IT/Consultant/Referral"
    #     )

    candidate.status = new
    candidate.save()

    # 4️⃣ Auto-advance the workflow if needed
    next_state = get_auto_next(new)
    if next_state:
        logger.info(f"AUTO: Moving {candidate.candidate_name} → {next_state}")
        candidate.status = next_state
        candidate.save()

        # IMPORTANT: Recursively process next state
        # So automation works like a chain reaction
        automation_engine(candidate, new, next_state)

    return True,""
