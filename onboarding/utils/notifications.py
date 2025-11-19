# notifications.py
import logging
from typing import Optional, Dict, Any
from .pdf_maker import generate_offer_letter
from .sender import send_email, send_text
from .templates import HTML_TEMPLATES
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Mapping: stage → notification configuration
# ----------------------------------------------------------------------

_NOTIFICATION_MAP: dict[str, dict[str, Any]] = {

    # --------------------------------------------------------------
    # 0. APPLICATION / DUPLICATE CHECK
    # --------------------------------------------------------------
    "applied": {
        "email": {
            "subject": "Application Received",
            "text": "Thank you for applying! Your application has been received and is under review.",
        },
        "sms": "Application received. We'll review your profile shortly.",
        "log": "Application acknowledgment sent to {candidate.email}",
    },
    "duplicate_rejected": {
        "email": {
            "subject": "Duplicate Application",
            "text": (
                "Thank you for your interest. Our records show that you have applied recently, "
                "so we cannot process this application as per our policy."
            ),
        },
        "sms": "Your profile already exists in our system.",
        "log": "Duplicate rejection sent to {candidate.email}",
    },

    # --------------------------------------------------------------
    # 1. SHORTLIST + INTERVIEW FLOW
    # --------------------------------------------------------------
    "shortlisted": {
        "email": {
            "subject": "You Have Been Shortlisted!",
            "text": "You have been shortlisted and will move to the interview stage.",
        },
        "sms": "You have been shortlisted! HR will schedule interview soon.",
        "log": "Shortlisting notification sent to {candidate.email}",
    },
    "interview_pending": {
        "email": {
            "subject": "Interview Scheduled",
            "text": "Your interview has been scheduled. Check your email for details.",
        },
        "sms": "Interview scheduled. Check email for timing/link.",
        "log": "Interview pending notification sent to {candidate.email}",
    },
    "interview_done": {
        "email": {
            "subject": "Thank You for Interviewing",
            "text": "Thank you for attending the interview. We are reviewing the results.",
        },
        "sms": "Thanks for interviewing! You’ll be updated soon.",
        "log": "Interview completion message sent to {candidate.email}",
    },
    "interview_rejected": {
        "email": {
            "subject": "Interview Update",
            "text": "We appreciate your time. Unfortunately, we will not move ahead at this time.",
        },
        "sms": "We will not move ahead with your application.",
        "log": "Interview rejection sent to {candidate.email}",
    },

    # --------------------------------------------------------------
    # 2. SELECTION & APPROVAL FLOW
    # --------------------------------------------------------------
    "selected": {
        "email": {
            "subject": "Congratulations – You’re Selected!",
            "text": "You have been selected by the interview panel. Awaiting approval.",
        },
        "sms": "Congrats! You’ve been selected. Approval process started.",
        "log": "Selection notification sent to {candidate.email}",
    },
    "approval_pending": {
        "email": {
            "subject": "Profile Sent for Approval",
            "text": "Your profile has been sent for approval.",
        },
        "sms": "Your profile is under approval.",
        "log": "Approval pending notification sent to {candidate.email}",
    },
    "approved": {
        "email": {
            "subject": "Profile Approved",
            "text": "Your profile has been approved. Offer letter will be prepared.",
        },
        "sms": "Profile approved! Offer preparation started.",
        "log": "Approval confirmation sent to {candidate.email}",
    },
    "approval_rejected": {
        "email": {
            "subject": "Application Update",
            "text": "Your profile was not approved by the hiring manager.",
        },
        "sms": "Your profile was not approved.",
        "log": "Approval rejection sent to {candidate.email}",
    },
    
    # ---------------------------- NEW NOTIFICATION BLOCKS ----------------------------
    "salary_docs_pending": {
        "email": {
            "subject": "Upload Salary Documents",
            "text": "Please upload your latest salary slip and bank statement.",
        },
        "sms": "Please upload your salary slip and bank statement.",
        "log": "Salary document upload request sent to {candidate.email}",
    },

    "salary_docs_uploaded": {
        "email": {
            "subject": "Salary Documents Received",
            "text": "We have received your salary slip and bank statement. HR will review them shortly.",
        },
        "sms": "Salary documents received.",
        "log": "Salary documents uploaded confirmation sent to {candidate.email}",
    },

    "hr_review_docs": {
        "email": {
            "subject": "HR Reviewing Documents",
            "text": "HR is reviewing your uploaded salary documents.",
        },
        "sms": "HR is reviewing your salary documents.",
        "log": "HR review of salary documents started for {candidate.email}",
    },

    "salary_annexure_prep": {
        "email": {
            "subject": "Salary Annexure Under Preparation",
            "text": "HR is preparing your salary annexure based on the verified documents.",
        },
        "sms": "HR is preparing your salary annexure.",
        "log": "Salary annexure preparation started for {candidate.email}",
    },

    "approved_annexure": {
        "email": {
            "subject": "Salary Annexure Approved",
            "text": "Your salary annexure has been approved by HR Head. Offer letter will be prepared next.",
        },
        "sms": "Salary annexure approved. Offer letter preparation started.",
        "log": "Salary annexure approval sent to {candidate.email}",
    },

    # --------------------------------------------------------------
    # 3. OFFER FLOW
    # --------------------------------------------------------------
    "offer_pending": {
        "email": {
            "subject": "Offer Preparation in Progress",
            "text": "We are preparing your offer letter.",
        },
        "sms": "Your offer is being prepared.",
        "log": "Offer pending notification sent to {candidate.email}",
    },
    "offer_sent": {
        "email": {
            "subject": "Your Offer Letter",
            "text": "Please find your offer letter attached.",
            "attachments_factory": generate_offer_letter,
        },
        "sms": "Your offer letter has been emailed to you.",
        "log": "Offer letter sent to {candidate.email}",
    },
    "offer_accepted": {
        "email": {
            "subject": "Offer Accepted",
            "text": "Thank you for accepting the offer! Please upload your resignation letter.",
        },
        "sms": "Offer accepted! Please upload your resignation letter.",
        "log": "Offer acceptance notification sent to {candidate.email}",
    },
    "offer_rejected": {
        "email": {
            "subject": "Update on Your Offer",
            "text": "You have declined the offer. Application closed.",
        },
        "sms": "You declined the offer.",
        "log": "Offer rejection notification sent to {candidate.email}",
    },

    # --------------------------------------------------------------
    # 4. RESIGNATION FLOW (NEW)
    # --------------------------------------------------------------
    "resignation_pending": {
        "email": {
            "subject": "Upload Your Resignation Letter",
            "text": "Please upload your resignation letter using this link: {link}",
        },
        "sms": "Upload your resignation letter: {link}",
        "log": "Resignation letter request sent to {candidate.email}",
    },
    "resignation_uploaded": {
        "email": {
            "subject": "Resignation Letter Received",
            "text": "We have received your resignation letter. HR will verify it shortly.",
        },
        "sms": "Resignation letter received.",
        "log": "Resignation uploaded confirmation sent to {candidate.email}",
    },
    "resignation_approved": {
        "email": {
            "subject": "Resignation Letter Approved",
            "text": "Your resignation letter has been approved. Please upload the required documents.",
        },
        "sms": "Resignation approved. Please upload required documents.",
        "log": "Resignation approved notification sent to {candidate.email}",
    },
    "resignation_rejected": {
        "email": {
            "subject": "Resignation Letter Rejected",
            "text": "Your resignation letter is unclear or incomplete. Please re-upload.",
        },
        "sms": "Resignation rejected. Please re-upload.",
        "log": "Resignation rejected notification sent to {candidate.email}",
    },

    # --------------------------------------------------------------
    # 5. DOCUMENT FLOW (UPDATED)
    # --------------------------------------------------------------
    "docs_pending": {
        "email": {
            "subject": "Upload Your Documents",
            "text": "Please upload your joining documents using this link: {link}",
        },
        "sms": "Upload your documents: {link}",
        "log": "Document upload request sent to {candidate.email}",
    },
    "docs_uploaded": {
        "email": {
            "subject": "Documents Received",
            "text": "We’ve received your documents. Verification will be done shortly.",
        },
        "sms": "Documents received.",
        "log": "Documents uploaded confirmation sent to {candidate.email}",
    },
    "docs_incomplete": {
        "email": {
            "subject": "Document Verification Result",
            "text": "Some documents were incomplete or unclear. Please re-upload using the same link.",
        },
        "sms": "Some documents were unclear. Please re-upload.",
        "log": "Documents incomplete notification sent to {candidate.email}",
    },
    "docs_approved": {
        "email": {
            "subject": "Documents Approved",
            "text": "All documents verified successfully. Joining process will begin.",
        },
        "sms": "Documents approved. Joining process started.",
        "log": "Documents approved notification sent to {candidate.email}",
    },

    # --------------------------------------------------------------
    # 6. JOINING FLOW
    # --------------------------------------------------------------
    "joining_pending": {
        "email": {
            "subject": "Joining Preparation Started",
            "text": "HR is preparing your onboarding formalities.",
        },
        "sms": "Joining formalities in progress.",
        "log": "Joining pending notification sent to {candidate.email}",
    },
    "joined": {
        "email": {
            "subject": "Welcome Aboard!",
            "text": "Congratulations on joining our team!",
        },
        "sms": "Welcome aboard!",
        "log": "Joining confirmation sent to {candidate.email}",
    },

    # --------------------------------------------------------------
    # FINAL
    # --------------------------------------------------------------
    "rejected": {
        "email": {
            "subject": "Application Update",
            "text": "Your application has been closed.",
        },
        "sms": "Your application has been closed.",
        "log": "Final rejection sent to {candidate.email}",
    },
}

def notify_candidate(candidate: Any, stage: str,cc:list) -> bool:
    """
    Unified notification dispatcher.

    Parameters
    ----------
    candidate : Any
        Object that must expose at least ``email`` and optionally ``name`` and ``phone``.
    stage : str
        One of the keys defined in ``_NOTIFICATION_MAP`` (or any value you add there).

    Returns
    -------
    bool
        ``True`` if **all** requested channels succeeded, ``False`` otherwise.
    """
    cfg = _NOTIFICATION_MAP.get(stage)
    if not cfg:
        logger.warning("No notification config for stage '%s'", stage)
        return False

    success = True

    email_cfg = cfg.get("email")
    sms_text = cfg.get("sms")
    # ---------- EMAIL ----------
    
    if email_cfg:
        attachments = []
        attach_factory = email_cfg.get("attachments_factory")
        if attach_factory:
            try:
                pdf = attach_factory(candidate)
                attachments = [pdf]
            except Exception as exc:
                logger.error("Failed to generate attachment for %s: %s", candidate.email, exc)
                success = False

        try:
            html_template = HTML_TEMPLATES[stage]
            if stage == 'docs_pending':
                link = f"https://9bd6882f3e08.ngrok-free.app/api/candidates/{candidate.id}/documents/upload/"
                email_cfg["text"].format(link=link)
                sms_text.format(link=link)
            send_email(
                to=candidate.email,
                subject=email_cfg["subject"],
                text=email_cfg["text"],
                cc= cc,
                template=html_template.format(candidate=candidate),
                attachments=attachments,
            )
        except Exception as exc:
            logger.exception("Email failed for %s (stage=%s): %s", candidate.email, stage, exc)
            success = False

    # ---------- SMS ----------
    
    if sms_text and getattr(candidate, "phone", None):
        try:
            send_text(candidate.phone, sms_text)
        except Exception as exc:
            logger.exception("SMS failed for %s (stage=%s): %s", candidate.phone, stage, exc)
            success = False

    # ---------- LOG ----------
    log_msg = cfg.get("log")
    if log_msg:
        try:
            # Allow simple {candidate.attr} placeholders
            formatted = log_msg.format(candidate=candidate)
            logger.info(formatted)
        except Exception as exc:
            logger.exception("Log formatting failed: %s", exc)

    return success