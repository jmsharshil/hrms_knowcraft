ALLOWED_TRANSITIONS = {
    # APPLICATION
    "applied": ["duplicate_rejected", "shortlisted"],
    # SHORTLISTING & INTERVIEW
    "shortlisted": ["interview_pending"],
    "interview_pending": ["interview_done"],
    "interview_done": ["selected", "interview_rejected"],
    # APPROVAL
    "selected": ["approval_pending"],
    "approval_pending": ["approved", "approval_rejected"],
    # OFFER FLOW
    # "approved": ["offer_pending"],
    "approved": ["salary_docs_pending"],
    "salary_docs_pending": ["salary_docs_uploaded"],
    # Candidate uploads Salary Slip + Bank Statement
    "salary_docs_uploaded": ["hr_review_docs"],

    # HR reviews uploaded documents
    # If rejected → back to upload_documents (re-upload)
    "hr_review_docs": ["salary_annexure_prep", "upload_documents"],

    # HR prepares salary annexure
    "salary_annexure_prep": ["approved_annexure"],

    # HR head approves salary annexure
    # If rejected → back to salary_annexure_preparation
    "approved_annexure": ["offer_pending", "salary_annexure_prep"],
    "offer_pending": ["offer_sent"],
    "offer_sent": ["offer_accepted", "offer_rejected"],
    # AFTER OFFER ACCEPTANCE → RESIGNATION FLOW
    "offer_accepted": ["resignation_pending"],
    "resignation_pending": ["resignation_uploaded"],
    "resignation_uploaded": ["resignation_approved", "resignation_rejected"],
    "resignation_rejected": ["resignation_pending"],  # retry upload
    # DOCUMENT COLLECTION
    "resignation_approved": ["docs_pending"],
    "docs_pending": ["docs_uploaded"],
    "docs_uploaded": ["docs_approved", "docs_incomplete"],
    "docs_incomplete": ["docs_pending"],  # reupload
    # JOINING
    "docs_approved": ["joining_pending"],
    "joining_pending": ["joined"],
    # TERMINAL
    "duplicate_rejected": [],
    "interview_rejected": [],
    "approval_rejected": [],
    "offer_rejected": [],
    "joined": []
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

    # "shortlisted":"interview_pending",
    "approved":"offer_pending",
    "offer_pending":"offer_sent",
    # "offer_accepted": "docs_pending",
    "offer_accepted": "resignation_pending",
    "resignation_approved": "docs_pending",
    "docs_approved": "joining_pending",
    # "docs_received": "joining_pending",
    "selected":"approval_pending"
}

def get_auto_next(stage):
    return AUTO_NEXT.get(stage)
