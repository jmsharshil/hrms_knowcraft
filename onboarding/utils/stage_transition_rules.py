ALLOWED_TRANSITIONS = {
    # APPLICATION
    "received": ["duplicate_rejected", "shortlisted"],
    # SHORTLISTING & INTERVIEW
    "shortlisted": ["interview_pending_1"],
    "interview_pending_1": ["interview_done_1"],
    "interview_done_1": ["interview_next_2","interview_next_3","interview_next_final", "interview_rejected_1","consolidated_result_review","interview_next_management_client"],
    "interview_next_2":["interview_pending_2","interview_rejected_1"],
    "interview_pending_2": ["interview_done_2"],
    "interview_done_2": ["interview_next_final","interview_next_3", "interview_rejected_2","consolidated_result_review","interview_next_management_client"],
    "interview_next_3":["interview_pending_3","interview_rejected_2"],
    "interview_pending_3": ["interview_done_3"],
    "interview_done_3": ["interview_next_final", "interview_rejected_3","consolidated_result_review","interview_next_management_client"],
    "interview_next_final":["interview_pending_final","interview_rejected_3"],
    "interview_pending_final": ["interview_done_final"],
    "interview_done_final": ["consolidated_result_review", "interview_rejected_final","interview_next_management_client"],
    "interview_next_management_client": ['interview_pending_management_client','interview_rejected_final'],
    "interview_pending_management_client":["interview_done_management_client"],
    "interview_done_management_client":["consolidated_result_review","interview_rejected_management_client"],
    # APPROVAL
    "consolidated_result_review":['selected','rejected'],
    "selected": ["approval_pending"],
    "approval_pending": ["approved", "approval_rejected"],
    # OFFER FLOW
    "approved": ["docs_pending"],
    "docs_pending": ["docs_uploaded"],
    "docs_uploaded":["review_docs"],
    "review_docs": ["docs_approved", "docs_incomplete","docs_unclear"],
    "docs_incomplete": ["docs_pending","docs_approved"],  # reupload
    "docs_unclear": ["docs_pending","docs_approved"],  # reupload
    "docs_approved": ["salary_annexure_prep","offer_pending"],
    # HR prepares salary annexure
    "salary_annexure_prep": ["salary_annexure_review","offer_sent"],
    "salary_annexure_review":["approved_annexure","rejected_annexure"],
    "rejected_annexure":["salary_annexure_prep"],
    # HR head approves salary annexure
    # If rejected → back to salary_annexure_preparation
    "approved_annexure": ["offer_pending"],
    "offer_pending": ["offer_sent"],
    "offer_sent": ["offer_accepted", "offer_rejected"],
    # AFTER OFFER ACCEPTANCE
    "offer_accepted": ["joining_pending"],
    # JOINING
    "joining_pending": ["joined","rejected","joining_poned"],
    "joining_poned":["joined","joining_pending","rejected"],
    # TERMINAL
    "duplicate_rejected": ["shortlisted"],
    "interview_rejected_1": ["interview_next_2","selected"],
    "interview_rejected_2": ["interview_next_3","selected"],
    "interview_rejected_3": ["interview_next_final","selected"],
    "interview_rejected_final": ["selected"],
    "interview_rejected_management_client":['selected'],
    "approval_rejected": ["selected"],
    "offer_rejected": ["selected"],
    "joined": [],
    "rejected": ["selected"]
}

def validate_transition(old, new):
    """
    Validate if a stage transition is allowed according to ALLOWED_TRANSITIONS.
    Returns (True, None) if valid.
    Returns (False, "reason") if invalid.
    """

    # If same stage → allowed (idempotent)
    if old == new:
        return True, None

    # Unknown stages
    if old not in ALLOWED_TRANSITIONS:
        return False, f"Unknown current stage: {old}"

    if new not in ALLOWED_TRANSITIONS:
        return False, f"Unknown new stage: {new}"

    allowed = ALLOWED_TRANSITIONS.get(old, [])

    if new in allowed:
        return True, None

    # Build helpful explanation
    reason = (
        f"Invalid transition: '{old}' → '{new}'. "
        f"Allowed next stages: {', '.join(allowed) or 'None (terminal stage)'}."
    )
    return False, reason


AUTO_NEXT = {
    "approved": "docs_pending",
    # "docs_approved": "salary_annexure_prep",
    "resignation_uploaded":"resignation_review",
    "docs_uploaded":"review_docs",
    "offer_accepted": "joining_pending"
    # "joining_postponed": "joining_pending",
}

def get_auto_next(stage):
    return AUTO_NEXT.get(stage)
