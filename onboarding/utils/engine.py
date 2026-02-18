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
    # "shortlisted",
    # "interview_pending_1",
    # "interview_done_1",
    "interview_rejected_1",
    # "interview_next_2",
    # "interview_pending_2",
    # "interview_done_2",
    "interview_rejected_2",
    # "interview_next_3",
    # "interview_pending_3",
    # "interview_done_3",
    "interview_rejected_3",
    # "interview_next_final",
    # "interview_pending_final",
    # "interview_done_final",
    "interview_rejected_final",
    # "interview_next_management_client",
    # "interview_pending_management_client",
    # "interview_done_management_client",
    "interview_rejected_management_client",
    # Approval
    # "approved",
    # "approval_rejected",
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
    # "offer_sent",
    "offer_accepted",
    "offer_rejected",
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
    "shortlisted",
    "interview_next_2",
    "interview_next_3",
    "interview_next_final",
    # "interview_pending_1",
    # "interview_pending_2",
    # "interview_pending_3",
    # "interview_pending_final",
    # "interview_done_1",
    # "interview_done_2",
    # "interview_done_3",
    # "interview_done_final",
    "interview_rejected_1",
    "interview_rejected_2",
    "interview_rejected_3",
    "interview_rejected_final",
    "interview_next_management_client",
    # "interview_pending_management_client",
    # "interview_done_management_client",
    "interview_rejected_management_client",
    # Approval Flow
    # "approval_pending",        # Send approval request to HR Manager
    "approved",                # Notify HR
    "approval_rejected",       # Notify HR
    # Salary Annexure Flow
    # "salary_annexure_prep",    # Notify HR to prepare annexure
    # "salary_annexure_sent",    # Notify HR manager
    # "approved_annexure",       # Notify HR
    # "rejected_annexure",       # Notify HR
    # Offer Flow (Internal Steps)
    # "offer_pending",           # Notify HR to prepare offer
    "offer_rejected",
    # Document Verification
    "docs_uploaded",           # HR reviews
    # Joining
    "joining_pending",         # Notify HR/IT/Admin internally
    "joining_poned",           # Internal delay notice
    "joined",                  # Broadcast to departments
    # Duplicate or general rejection internal notices
    # "duplicate_rejected",
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
    if new == 'shortlisted':
        candidate.is_shortlisted = True
    if new == 'selected':
        candidate.is_selected = True
    if new == 'rejected':
        candidate.is_rejected = True
    if new == 'approved':
        candidate.is_approved = True
    candidate.save()

    from slots.models import Interviewer
    interviewer_email, interviewer = None, None
    if new == 'shortlisted':
        interviewer_email = candidate.job.mrf.interviewer_email_1
    elif new == "interview_next_2":
        interviewer_email = candidate.job.mrf.interviewer_email_2
    elif new == "interview_next_3":
        interviewer_email = candidate.job.mrf.interviewer_email_3
    elif new == "interview_next_final":
        interviewer_email = candidate.job.mrf.interviewer_email_final
    elif new == "interview_next_management_client":
        interviewer_email = candidate.job.mrf.interviewer_email_management_client
    if interviewer_email:
        interviewer = Interviewer.objects.filter(email=interviewer_email).first()
    interviewer_id = interviewer.id if interviewer else None
    if interviewer_id:
        candidate.slot_link = (
            f"https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net/api/slots/available/?candidate_id={candidate.id}&interviewer_id={interviewer_id}"
        )
    else:
        candidate.slot_link = ""

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
