ALLOWED_TRANSITIONS = {
    # APPLICATION
    "received": ["duplicate_rejected", "shortlisted"],
    # "duplicate_rejected": ["applied"],
    # SHORTLISTING & INTERVIEW
    "shortlisted": ["interview_pending_1"],
    "interview_pending_1": ["interview_done_1"],
    "interview_done_1": ["interview_next_2","interview_next_final", "interview_rejected_1","selected"],
    "interview_next_2":["interview_pending_2","interview_rejected_1"],
    "interview_pending_2": ["interview_done_2"],
    "interview_done_2": ["interview_next_final","interview_next_3", "interview_rejected_2","selected"],
    "interview_next_3":["interview_pending_3","interview_rejected_2"],
    "interview_pending_3": ["interview_done_3"],
    "interview_done_3": ["interview_next_final", "interview_rejected_3","selected"],
    "interview_next_final":["interview_pending_final","interview_rejected_3"],
    "interview_pending_final": ["interview_done_final"],
    "interview_done_final": ["selected", "interview_rejected_final"],
    # APPROVAL
    "selected": ["approval_pending"],
    "approval_pending": ["approved", "approval_rejected"],
    # OFFER FLOW
    "approved": ["salary_docs_pending"],
    "salary_docs_pending": ["salary_docs_uploaded"],
    # Candidate uploads Salary Slip + Bank Statement
    "salary_docs_uploaded": ["hr_review_docs"],
    # HR reviews uploaded documents
    # If rejected → back to upload documents (re-upload)
    "hr_review_docs": ["hr_review_ok","hr_review_rejected"],
    "hr_review_rejected":["salary_docs_pending","rejected"],
    "hr_review_ok" : ["salary_annexure_prep"],
    # HR prepares salary annexure
    "salary_annexure_prep": ["salary_annexure_sent"],
    "salary_annexure_sent":["approved_annexure","rejected_annexure"],
    "rejected_annexure":["salary_annexure_prep"],
    # HR head approves salary annexure
    # If rejected → back to salary_annexure_preparation
    "approved_annexure": ["offer_pending"],
    "offer_pending": ["offer_sent"],
    "offer_sent": ["offer_accepted", "offer_rejected"],
    # AFTER OFFER ACCEPTANCE → RESIGNATION FLOW
    "offer_accepted": ["resignation_pending"],
    "resignation_pending": ["resignation_uploaded"],
    "resignation_uploaded":["resignation_review"],
    "resignation_review": ["resignation_approved", "resignation_rejected"],
    "resignation_rejected": ["resignation_pending","rejected"],  # retry upload
    # DOCUMENT COLLECTION
    "resignation_approved": ["docs_pending"],
    "docs_pending": ["docs_uploaded"],
    "docs_uploaded":["review_docs"],
    "review_docs": ["docs_approved", "docs_incomplete","docs_unclear"],
    "docs_incomplete": ["docs_pending"],  # reupload
    "docs_unclear": ["docs_pending"],  # reupload
    # JOINING
    "docs_approved": ["joining_pending"],
    "joining_pending": ["joined","rejected","joining_poned"],
    "joining_poned":["joined","joining_pending","rejected"],
    # TERMINAL
    "duplicate_rejected": ["shortlisted"],
    "interview_rejected_1": ["interview_next_2","selected"],
    "interview_rejected_2": ["interview_next_3","selected"],
    "interview_rejected_3": ["interview_next_final","selected"],
    "interview_rejected_final": ["selected"],
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

    # "shortlisted":"interview_pending",
    "approved": "salary_docs_pending",
    "salary_docs_uploaded": "hr_review_docs",
    "hr_review_ok": "salary_annexure_prep",
    # "salary_annexure_prep":"salary_annexure_sent",
    "approved_annexure":"offer_pending",
    "offer_pending":"offer_sent",
    "offer_accepted": "resignation_pending",
    "resignation_approved": "docs_pending",
    "docs_approved": "joining_pending",
    "selected":"approval_pending",
    "resignation_uploaded":"resignation_review",
    "docs_uploaded":"review_docs",
    "docs_incomplete":"docs_pending",
    "docs_unclear": "docs_pending",
    # "joining_postponed": "joining_pending",
}

def get_auto_next(stage):
    return AUTO_NEXT.get(stage)
