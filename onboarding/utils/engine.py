# engine.py
import logging
from .stage_transition_rules import get_auto_next, validate_transition
from .notifications import notify_candidate

logger = logging.getLogger(__name__)


# ------------------------------
# Notification rules for ALL STATES
# ------------------------------
NOTIFY_STATES = {
    "shortlisted",
    "interview_pending",
    "interview_done",
    "interview_rejected",

    # "selected",
    # "approval_pending",
    "approved",
    "approval_rejected",

    "offer_pending",
    "offer_sent",
    "offer_accepted",
    "offer_rejected",

    "docs_pending",
    "docs_received",
    "joining_pending",
    "joined",

    "duplicate_rejected",
    "rejected",
}


# ------------------------------
# Broadcast rules for internal teams
# ------------------------------
BROADCAST_ON_JOIN = True


def automation_engine(candidate, old, new):
    logger.info(f"AUTO: {candidate.name} {old} → {new}")

    # 1️⃣ Validate transition
    ok, reason = validate_transition(old, new)
    if not ok:
        logger.error(f"❌ Invalid transition: {old} → {new}. Reason: {reason}")
        return False,reason

    # 2️⃣ Send candidate notifications (if applicable)
    if new in NOTIFY_STATES:
        try:
            notify_candidate(candidate, new,cc=[])
            logger.info(f"AUTO: Notification sent for {candidate.name} → {new}")
        except Exception as e:
            logger.exception(f"❌ Error sending notification: {e}")

    # 3️⃣ Internal broadcasting for key events
    if new == "joined" and BROADCAST_ON_JOIN:
        logger.info(
            f"AUTO: Broadcasting joining of {candidate.name} to Head/HR/Finance/IT/Consultant/Referral"
        )

    candidate.stage = new
    candidate.save()
    # 4️⃣ Auto-advance the workflow if needed
    next_state = get_auto_next(new)
    if next_state:
        logger.info(f"AUTO: Moving {candidate.name} → {next_state}")
        candidate.stage = next_state
        candidate.save()

        # IMPORTANT: Recursively process next state
        # So automation works like a chain reaction
        automation_engine(candidate, new, next_state)

    return True,""
