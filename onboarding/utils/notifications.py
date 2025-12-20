# notifications.py
import logging
from typing import Optional, Dict, Any
from .pdf_maker import generate_offer_letter
from .sender import send_email, send_text
from .templates import HTML_TEMPLATES
from .opensign import send_to_opensign_and_get_link
from accounts.models import User
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Mapping: stage → notification configuration
# ----------------------------------------------------------------------

_NOTIFICATION_MAP: dict[str, dict[str, Any]] = {

    # --------------------------------------------------------------
    # 0. APPLICATION / DUPLICATE CHECK
    # --------------------------------------------------------------
    "received": {
        "email": {
            "subject": "Application Received",
            "text": "Thank you for applying! Your application has been received and is under review.",
        },
        "sms": "Application received. We'll review your profile shortly.",
        "log": "Application acknowledgment sent to {candidate.candidate_email}",
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
        "log": "Duplicate rejection sent to {candidate.candidate_email}",
    },

    # --------------------------------------------------------------
    # 1. SHORTLIST + INTERVIEW FLOW
    # --------------------------------------------------------------
    "shortlisted": {
        "email": {
            "subject": "You Have Been Shortlisted!",
            "text": "You have been shortlisted and will move to the interview stage.Please select interview slot from using given link : {schedule_link}",
        },
        "sms": "You have been shortlisted! Schedule your interview by selecting the time slot using this link: {schedule_link}.",
        "log": "Shortlisting notification sent to {candidate.candidate_email}",
        "schedule_link":True
    },
    "interview_pending_1": {
        "email": {
            "subject": "Interview Scheduled",
            "text": "Your interview has been scheduled. Check your email for details.",
        },
        "sms": "Interview scheduled. Check email for timing/link.",
        "log": "Interview pending notification sent to {candidate.candidate_email}",
    },
    "interview_done_1": {
        "email": {
            "subject": "Thank You for Interviewing",
            "text": "Thank you for attending the interview. We are reviewing the results.",
        },
        "sms": "Thanks for interviewing! You’ll be updated soon.",
        "log": "Interview completion message sent to {candidate.candidate_email}",
    },
    "interview_rejected_1": {
        "email": {
            "subject": "Interview Update",
            "text": "We appreciate your time. Unfortunately, we will not move ahead at this time.",
        },
        "sms": "We will not move ahead with your application.",
        "log": "Interview round 1 rejection sent to {candidate.candidate_email}",
    },
    "interview_next_2": {
        "email": {
            "subject": "Interview Second Round",
            "text": "You have been shortlisted for second round of interview.Please select interview slot from using given link : {schedule_link}",
        },
        "sms": "You have been shortlisted for second round of interview! Schedule your interview by selecting the time slot using this link: {schedule_link}.",
        "log": "Round 2 notification sent to {candidate.candidate_email}",
        "schedule_link":True
    },
    "interview_pending_2": {
        "email": {
            "subject": "Interview Scheduled",
            "text": "Your interview for round 2 has been scheduled. Check your email for details.",
        },
        "sms": "Interview for round 2 has been scheduled. Check email for timing/link.",
        "log": "Interview round 2 pending notification sent to {candidate.candidate_email}",
    },
    "interview_done_2": {
        "email": {
            "subject": "Thank You for Interviewing",
            "text": "Thank you for attending the interview. We are reviewing the results.",
        },
        "sms": "Thanks for interviewing! You’ll be updated soon.",
        "log": "Interview round 2 completion message sent to {candidate.candidate_email}",
    },
    "interview_rejected_2": {
        "email": {
            "subject": "Interview Update",
            "text": "We appreciate your time. Unfortunately, we will not move ahead at this time.",
        },
        "sms": "We will not move ahead with your application.",
        "log": "Interview rejection for round 2 sent to {candidate.candidate_email}",
    },
    "interview_next_final": {
        "email": {
            "subject": "Final Round interview",
            "text": "You have been shortlisted for final round.Please select interview slot from using given link : {schedule_link}",
        },
        "sms": "You have been shortlisted for final round! Schedule your interview by selecting the time slot using this link: {schedule_link}.",
        "log": "Final Round selection notification sent to {candidate.candidate_email}",
        "schedule_link":True
    },
    "interview_pending_final": {
        "email": {
            "subject": "Interview Scheduled",
            "text": "Your interview for round 3 has been scheduled. Check your email for details.",
        },
        "sms": "Interview round 3 has been scheduled. Check email for timing/link.",
        "log": "Final Interview pending notification sent to {candidate.candidate_email}",
    },
    "interview_done_final": {
        "email": {
            "subject": "Thank You for Interviewing",
            "text": "Thank you for attending the interview. We are reviewing the results.",
        },
        "sms": "Thanks for interviewing! You’ll be updated soon.",
        "log": "Final Interview completion message sent to {candidate.candidate_email}",
    },
    "interview_rejected_final": {
        "email": {
            "subject": "Interview Update",
            "text": "We appreciate your time. Unfortunately, we will not move ahead at this time.",
        },
        "sms": "We will not move ahead with your application.",
        "log": "Interview rejection for final round sent to {candidate.candidate_email}",
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
        "log": "Selection notification sent to {candidate.candidate_email}",
    },
    "approval_pending": {
        "email": {
            "subject": "Profile Sent for Approval",
            "text": "Your profile has been sent for approval.",
        },
        "sms": "Your profile is under approval.",
        "log": "Approval pending notification sent to {candidate.candidate_email}",
    },
    "approved": {
        "email": {
            "subject": "Profile Approved",
            "text": "Your profile has been approved. Offer letter will be prepared.",
        },
        "sms": "Profile approved! Offer preparation started.",
        "log": "Approval confirmation sent to {candidate.candidate_email}",
    },
    "approval_rejected": {
        "email": {
            "subject": "Application Update",
            "text": "Your profile was not approved by the hiring manager.",
        },
        "sms": "Your profile was not approved.",
        "log": "Approval rejection sent to {candidate.candidate_email}",
    },
    
    # ---------------------------- NEW NOTIFICATION BLOCKS ----------------------------
    "salary_docs_pending": {
        "email": {
            "subject": "Upload Salary Documents",
            "text": "Please upload your latest salary slip and bank statement.",
        },
        "sms": "Please upload your salary slip and bank statement.",
        "log": "Salary document upload request sent to {candidate.candidate_email}",
    },

    "salary_docs_uploaded": {
        "email": {
            "subject": "Salary Documents Received",
            "text": "We have received your salary slip and bank statement. HR will review them shortly.",
        },
        "sms": "Salary documents received.",
        "log": "Salary documents uploaded confirmation sent to {candidate.candidate_email}",
    },

    "hr_review_docs": {
        "email": {
            "subject": "HR Reviewing Documents",
            "text": "HR is reviewing your uploaded salary documents.",
        },
        "sms": "HR is reviewing your salary documents.",
        "log": "HR review of salary documents started for {candidate.candidate_email}",
    },
    "hr_review_ok": {
        "email": {
            "subject": "Salary Documents Verified",
            "text": "Your salary documents have been verified successfully. HR will now prepare your salary annexure.",
        },
        "sms": "Salary documents verified. HR is preparing your salary annexure.",
        "log": "HR verified salary documents for {candidate.candidate_email}",
    },
    "hr_review_rejected": {
        "email": {
            "subject": "Salary Documents Rejected",
            "text": "Your uploaded salary documents were unclear or incorrect. Please re-upload them.",
        },
        "sms": "Salary documents rejected. Please re-upload.",
        "log": "HR rejected salary documents for {candidate.candidate_email}",
    },
    "salary_annexure_prep": {
        "email": {
            "subject": "Salary Annexure Under Preparation",
            "text": "HR is preparing your salary annexure based on the verified documents.",
        },
        "sms": "HR is preparing your salary annexure.",
        "log": "Salary annexure preparation started for {candidate.candidate_email}",
    },
    "salary_annexure_sent": {
        "email": {
            "subject": "Salary Annexure Sent for Approval",
            "text": "Your salary annexure has been sent to HR Head for approval.",
        },
        "sms": "Salary annexure sent for approval.",
        "log": "Salary annexure sent for approval for {candidate.candidate_email}",
    },
    "approved_annexure": {
        "email": {
            "subject": "Salary Annexure Approved",
            "text": "Your salary annexure has been approved by HR Head. Offer letter will be prepared next.",
        },
        "sms": "Salary annexure approved. Offer letter preparation started.",
        "log": "Salary annexure approval sent to {candidate.candidate_email}",
    },
    "rejected_annexure": {
        "email": {
            "subject": "Salary Annexure Rejected",
            "text": "The HR Head has requested changes. HR will update the annexure and resend.",
        },
        "sms": "Salary annexure rejected. HR will resend after correction.",
        "log": "Salary annexure rejected for {candidate.candidate_email}",
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
        "log": "Offer pending notification sent to {candidate.candidate_email}",
    },
    # "offer_sent": {
    #     "email": {
    #         "subject": "Your Offer Letter",
    #         "text": "Please find your offer letter attached.",
    #         "attachments_factory": generate_offer_letter,
    #     },
    #     "sms": "Your offer letter has been emailed to you.",
    #     "log": "Offer letter sent to {candidate.candidate_email}",
    # },
    "offer_sent": {
        "email": {
            "subject": "Your Offer Letter – Signature Required",
            "text": "Please sign your offer letter using the secure link provided: {sign_url}",
        },
        "sms": "Your offer letter is ready. Please check email to sign.",
        "opensign": True,   # <== IMPORTANT FLAG
        "log": "Offer letter sent for signing to {candidate.candidate_email}",
    },
    "offer_accepted": {
        "email": {
            "subject": "Offer Accepted",
            "text": "Thank you for accepting the offer! Please upload your resignation letter.",
        },
        "sms": "Offer accepted! Please upload your resignation letter.",
        "log": "Offer acceptance notification sent to {candidate.candidate_email}",
    },
    "offer_rejected": {
        "email": {
            "subject": "Update on Your Offer",
            "text": "You have declined the offer. Application closed.",
        },
        "sms": "You declined the offer.",
        "log": "Offer rejection notification sent to {candidate.candidate_email}",
    },

    # --------------------------------------------------------------
    # 4. RESIGNATION FLOW (NEW)
    # --------------------------------------------------------------
    "resignation_pending": {
        "email": {
            "subject": "Upload Your Resignation Letter",
            "text": "Please upload your resignation letter under 48 hours using this link: {link}",
        },
        "sms": "Upload your resignation letter under 48 hours using this link: {link}.",
        "log": "Resignation letter request sent to {candidate.candidate_email}",
    },
    "resignation_uploaded": {
        "email": {
            "subject": "Resignation Letter Received",
            "text": "We have received your resignation letter. HR will verify it shortly.",
        },
        "sms": "Resignation letter received.",
        "log": "Resignation uploaded confirmation sent to {candidate.candidate_email}",
    },
    "resignation_review": {
        "email": {
            "subject": "Resignation Letter Under Review",
            "text": "Your resignation letter is under review by HR.",
        },
        "sms": "Resignation letter is under review.",
        "log": "Resignation review started for {candidate.candidate_email}",
    },
    "resignation_approved": {
        "email": {
            "subject": "Resignation Letter Approved",
            "text": "Your resignation letter has been approved. Please upload the required documents.",
        },
        "sms": "Resignation approved. Please upload required documents.",
        "log": "Resignation approved notification sent to {candidate.candidate_email}",
    },
    "resignation_rejected": {
        "email": {
            "subject": "Resignation Letter Rejected",
            "text": "Your resignation letter is unclear or incomplete. Please re-upload.",
        },
        "sms": "Resignation rejected. Please re-upload.",
        "log": "Resignation rejected notification sent to {candidate.candidate_email}",
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
        "log": "Document upload request sent to {candidate.candidate_email}",
    },
    "docs_uploaded": {
        "email": {
            "subject": "Documents Received",
            "text": "We’ve received your documents. Verification will be done shortly.",
        },
        "sms": "Documents received.",
        "log": "Documents uploaded confirmation sent to {candidate.candidate_email}",
    },
    "review_docs": {
        "email": {
            "subject": "Document Verification in Progress",
            "text": "Your uploaded documents are under review. You'll be notified once verification is completed.",
        },
        "sms": "Documents under review.",
        "log": "Document review started for {candidate.candidate_email}",
    },
    "docs_unclear": {
        "email": {
            "subject": "Documents Unclear",
            "text": "Some uploaded documents were unclear. Please re-upload the required documents.",
        },
        "sms": "Documents unclear. Please re-upload.",
        "log": "Documents unclear notification sent to {candidate.candidate_email}",
    },
    "docs_incomplete": {
        "email": {
            "subject": "Document Verification Result",
            "text": "Some documents were incomplete or unclear. Please re-upload using the same link.",
        },
        "sms": "Some documents were unclear. Please re-upload.",
        "log": "Documents incomplete notification sent to {candidate.candidate_email}",
    },
    "docs_approved": {
        "email": {
            "subject": "Documents Approved",
            "text": "All documents verified successfully. Joining process will begin.",
        },
        "sms": "Documents approved. Joining process started.",
        "log": "Documents approved notification sent to {candidate.candidate_email}",
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
        "log": "Joining pending notification sent to {candidate.candidate_email}",
    },
    "joining_poned": {
        "email": {
            "subject": "Joining Postponed",
            "text": "Your joining has been postponed. HR will provide the updated joining date.",
        },
        "sms": "Joining postponed. Wait for updated date.",
        "log": "Joining postponed notification sent to {candidate.candidate_email}",
    },
    "joined": {
        "email": {
            "subject": "Welcome Aboard!",
            "text": "Congratulations on joining our team!",
        },
        "sms": "Welcome aboard!",
        "log": "Joining confirmation sent to {candidate.candidate_email}",
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
        "log": "Final rejection sent to {candidate.candidate_email}",
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
        # attach_factory = email_cfg.get("attachments_factory")
        # if attach_factory:
        #     try:
        #         pdf = attach_factory(candidate)
        #         attachments = [pdf]
        #     except Exception as exc:
        #         logger.error("Failed to generate attachment for %s: %s", candidate.candidate_email, exc)
        #         success = False
        sign_url = None
        if cfg.get("opensign"):
            try:
                # filename, pdf_bytes, mimetype = generate_offer_letter(candidate)

                # Call OpenSign API
                sign_url,form_id = send_to_opensign_and_get_link(candidate=candidate)
                from django.core.cache import cache
                cache.set(f"opensign_form_{form_id}", str(candidate.id), timeout=60*60*24)  # e.g. 24h

                # Inject URL into email text
                email_cfg["text"] = email_cfg["text"].format(sign_url=sign_url)

            except Exception as exc:
                logger.exception("Failed OpenSign flow: %s", exc)
                success = False
        schedule_link = None
        if cfg.get("schedule_link"):
            try:
                mrf = candidate.job.mrf
                from slots.models import Interviewer
                # from rest_framework.test import APIRequestFactory
                # from mrf.views import MRFViewSet
                # request = APIRequestFactory().get(f'api/mrf/mrfs/{mrf.id}/interviewers/')
                # response = MRFViewSet.as_view({'get':"list"})(request)
                # resp = response.data
                if stage == 'shortlisted':
                    # interviewer_id = resp['interviewers'][0]['interviewer_id']
                    interviewer_email = mrf.interviewer_email_1
                elif stage == "interview_next_2":
                    interviewer_email = mrf.interviewer_email_2
                    # interviewer_id = resp['interviewers'][1]['interviewer_id']
                elif stage == "interview_next_final":
                    interviewer_email = mrf.interviewer_email_final
                    # interviewer_id = resp['interviewers'][2]['interviewer_id']
                interviewer = Interviewer.objects.filter(email=interviewer_email).first()
                if interviewer:
                    interviewer_id = interviewer.id
                else:
                    interviewer_id = None
                schedule_link = (
                        f"http://localhost:5173/api/slots/available/"
                        f"?candidate_id={candidate.id}&interviewer_id={interviewer_id}"
                    )
                email_cfg["text"] = email_cfg["text"].format(schedule_link=schedule_link)
                sms_text.format(schedule_link=schedule_link)
            except Exception as e:
                print(e)
        try:
            html_template = HTML_TEMPLATES[stage]
            if stage == 'docs_pending' or stage == "resignation_pending" or stage == "salary_docs_pending":
                link = f"https://9bd6882f3e08.ngrok-free.app/api/candidates/{candidate.id}/documents/upload/"
                email_cfg["text"].format(link=link)
                sms_text.format(link=link)
            send_email(
                to=candidate.candidate_email,
                subject=email_cfg["subject"],
                text=email_cfg["text"],
                cc= cc,
                template=html_template.format(candidate=candidate,sign_url=sign_url,schedule_link=schedule_link),
                attachments=attachments,
            )
        except Exception as exc:
            logger.exception("Email failed for %s (stage=%s): %s", candidate.candidate_email, stage, exc)
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

NOTIFY_INTERNAL_MAP = {
    # "applied": {
    #     "receivers": ["consultant", "referer"],
    #     "subject": "New Candidate Application Received",
    #     "body": "A new candidate has applied and requires initial review.",
    #     "sms": "New candidate applied. Please review.",
    # },
    "interview_pending_1": {
        "receivers": ["interviewer"],
        "subject": "Interview Pending",
        "body": "The candidate is ready for interview scheduling.",
        "sms": "Interview pending for assigned candidate.",
    },
    "interview_pending_2": {
        "receivers": ["interviewer"],
        "subject": "Interview Pending",
        "body": "The candidate is ready for interview scheduling.",
        "sms": "Interview pending for assigned candidate.",
    },
    "interview_pending_final": {
        "receivers": ["interviewer"],
        "subject": "Interview Pending",
        "body": "The candidate is ready for interview scheduling.",
        "sms": "Interview pending for assigned candidate.",
    },
    # "interview_done_1": {
    #     "receivers": ["interviewer"],
    #     "subject": "Interview Pending",
    #     "body": "The candidate is ready for interview scheduling.",
    #     "sms": "Interview pending for assigned candidate.",
    # },
    # "interview_done_2": {
    #     "receivers": ["interviewer"],
    #     "subject": "Interview Pending",
    #     "body": "The candidate is ready for interview scheduling.",
    #     "sms": "Interview pending for assigned candidate.",
    # },
    # "interview_done_final": {
    #     "receivers": ["interviewer"],
    #     "subject": "Interview Pending",
    #     "body": "The candidate is ready for interview scheduling.",
    #     "sms": "Interview pending for assigned candidate.",
    # },
    "shortlisted": {
        "receivers": ["hr"],
        "subject": "Interview Pending",
        "body": "The candidate is ready for interview scheduling.",
        "sms": "Interview pending for assigned candidate.",
    },
    "interview_next_2": {
        "receivers": ["interviewer"],
        "subject": "Interview Pending",
        "body": "The candidate is ready for interview scheduling.",
        "sms": "Interview pending for assigned candidate.",
    },
    "interview_next_final": {
        "receivers": ["interviewer"],
        "subject": "Interview Pending",
        "body": "The candidate is ready for interview scheduling.",
        "sms": "Interview pending for assigned candidate.",
    },
    "interview_rejected_1": {
        "receivers": ["interviewer"],
        "subject": "Interview Pending",
        "body": "The candidate is ready for interview scheduling.",
        "sms": "Interview pending for assigned candidate.",
    },
    "interview_rejected_2": {
        "receivers": ["interviewer"],
        "subject": "Interview Pending",
        "body": "The candidate is ready for interview scheduling.",
        "sms": "Interview pending for assigned candidate.",
    },
    "interview_rejected_final": {
        "receivers": ["interviewer"],
        "subject": "Interview Pending",
        "body": "The candidate is ready for interview scheduling.",
        "sms": "Interview pending for assigned candidate.",
    },
    "approval_pending": {
        "receivers": ["hr_manager"],
        "subject": "Approval Required for Candidate",
        "body": "Candidate is pending managerial approval.",
        "sms": "Candidate approval required.",
    },
    "approved": {
        "receivers": ["hr"],
        "subject": "Candidate Approved",
        "body": "Candidate has been approved. Move to next steps.",
        "sms": "Candidate approved.",
    },
    "approval_rejected": {
        "receivers": ["hr"],
        "subject": "Candidate Approval Rejected",
        "body": "Approval manager has rejected the candidate’s profile.",
        "sms": "Candidate approval rejected.",
    },
    "salary_docs_uploaded": {
        "receivers": ["hr"],
        "subject": "Salary Documents Uploaded",
        "body": "Salary documents have been uploaded. Review required.",
        "sms": "Candidate salary documents uploaded.",
    },
    "salary_annexure_prep": {
        "receivers": ["hr"],
        "subject": "Prepare Salary Annexure",
        "body": "Start preparing the salary annexure for the candidate.",
        "sms": "Prepare salary annexure.",
    },
    "salary_annexure_sent": {
        "receivers": ["hr_manager"],
        "subject": "Salary Annexure Sent for Approval",
        "body": "Salary annexure has been sent for managerial approval.",
        "sms": "Salary annexure approval pending.",
    },
    "approved_annexure": {
        "receivers": ["hr"],
        "subject": "Salary Annexure Approved",
        "body": "Salary annexure has been approved.",
        "sms": "Salary annexure approved.",
    },
    "rejected_annexure": {
        "receivers": ["hr"],
        "subject": "Salary Annexure Rejected",
        "body": "Salary annexure has been rejected. Further action required.",
        "sms": "Salary annexure rejected.",
    },
    "offer_pending": {
        "receivers": ["hr"],
        "subject": "Offer Letter Pending",
        "body": "Prepare and send the offer letter to the candidate.",
        "sms": "Offer letter preparation pending.",
    },
    # "offer_accepted": {
    #     "receivers": ["hr"],
    #     "subject": "Offer Accepted by Candidate",
    #     "body": "Candidate has accepted the offer.",
    #     "sms": "Candidate accepted the offer.",
    # },
    "offer_rejected": {
        "receivers": ["consultancy"],
        "subject": "Offer Rejected",
        "body": "Candidate has rejected the offer.",
        "sms": "Candidate rejected the offer.",
    },
    "resignation_uploaded": {
        "receivers": ["hr"],
        "subject": "Resignation Uploaded",
        "body": "Candidate's resignation has been uploaded.",
        "sms": "Resignation document uploaded.",
    },
    "docs_uploaded": {
        "receivers": ["hr"],
        "subject": "Documents Uploaded",
        "body": "Candidate has uploaded joining documents.",
        "sms": "Candidate uploaded joining documents.",
    },
    "joining_pending": {
        "receivers": ["hr", "iternal_team", "admin", "department_head"],
        "subject": "Joining Pending",
        "body": "Candidate is pending joining. Prepare required steps.",
        "sms": "Candidate joining pending.",
    },
    "joining_poned": {
        "receivers": ["hr", "department_head"],
        "subject": "Joining Postponed",
        "body": "Candidate has postponed the joining date.",
        "sms": "Candidate postponed joining.",
    },
    "joined": {
        "receivers": ["hr", "iternal_team", "admin", "department_head", "consultancy", "referer"],
        "subject": "Candidate Joined",
        "body": "Candidate has joined successfully.",
        "sms": "Candidate joined.",
    },
    "duplicate_rejected": {
        "receivers": ["consultancy"],
        "subject": "Duplicate Profile Rejected",
        "body": "Candidate profile rejected due to duplication.",
        "sms": "Duplicate profile rejected.",
    },
    "rejected": {
        "receivers": ["consultancy", "department_head", "hr"],
        "subject": "Candidate Rejected",
        "body": "Candidate profile has been rejected.",
        "sms": "Candidate rejected.",
    },
}

def resolve_internal_emails(candidate, receivers: list[str]) -> list[str]:
    emails = set()

    job = candidate.job
    if not job:
        logger.error(f"No job linked with candidate {candidate.id}")
        return []
    try:

        for role in receivers:

            # HR (comes from MRF)
            if role == "hr":
                if job and job.assigned_to_internal_hr and job.assigned_to_internal_hr.email:
                    emails.add(job.assigned_to_internal_hr.email)
                    continue
            
            if role == "interviewer":
                if job and job.mrf:
                    if candidate.status in ["interview_pending_1","interview_done_1","interview_rejected_1","shorlisted"]:
                        emails.add(job.mrf.interviewer_email_1)
                    if candidate.status in ["interview_pending_1","interview_done_1","interview_rejected_1","interview_next_2"]:
                        emails.add(job.mrf.interviewer_email_2)
                    if candidate.status in ["interview_pending_1","interview_done_1","interview_rejected_1","interview_next_final"]:
                        emails.add(job.mrf.interviewer_email_final)
                    continue

            if role == "consultancy":
                if job and job.assigned_to_consultancy and job.assigned_to_consultancy.email:
                    emails.add(job.assigned_to_consultancy.email)
                    continue
            
            if role == 'department_head':
                if job and job.mrf and job.mrf.requested_by and job.mrf.requested_by.email:
                   emails.add(job.mrf.requested_by.email) 
                continue

            if role == 'hr_manager':
                if job and job.assigned_by and job.assigned_by.email:
                   emails.add(job.assigned_by.email) 
                continue

            if role == 'admin':
                admin = User.objects.filter(role='admin').exclude(email__isnull=True).exclude(email="").first()
                emails.add(admin.email)
                continue

            if role == "referer":
                # if candidate and candidate.referer:
                #     emails.add(candidate.referer)
                continue

            if role == "internal_team":
                #To be written 
                continue

        return list(emails)
    except Exception as e:
        logger.exception("Error finding emails to send:",e)

def notify_internal(candidate: Any, stage: str,cc:list) -> bool:
    recievers = NOTIFY_INTERNAL_MAP[stage]['receivers']
    subject = NOTIFY_INTERNAL_MAP[stage]['subject']
    body = NOTIFY_INTERNAL_MAP[stage]['body']
    sms_text = NOTIFY_INTERNAL_MAP[stage]['sms']

    if not recievers:
        logger.warning("No notification recievers for stage '%s'", stage)
        return False
    to_emails = resolve_internal_emails(candidate, recievers)

    if not to_emails:
        logger.warning(f"No internal email recipients found for stage {stage}")
        return False
    try:
        from .templates import NOTIFY_INTERNAL_HTML_TEMPLATES
        for email in to_emails:
            template = NOTIFY_INTERNAL_HTML_TEMPLATES[stage]
            feedback_link = None
            if stage in ['interview_pending_1','interview_pending_2',"interview_pending_final"]:
                if stage == 'interview_pending_1':
                    round = "hr_round"
                if stage == 'interview_pending_2':
                    round = "technical_round_1"
                if stage == 'interview_pending_final':
                    round = "technical_round_2"
                feedback_link = f"http://localhost:5173/api/slots/interview-feedback/?job_application={candidate.id}&interview_round={round}"
            template = template.format(candidate=candidate,feedback_link=feedback_link)
            send_email(email,subject=subject,text=body,template=template)
        logger.info(
            f"Internal notification sent for {candidate.candidate_name} at stage '{stage}' to {to_emails}"
        )
        return True
    except Exception as e:
        logger.exception(f"Failed internal notification: {e}")
        return False
