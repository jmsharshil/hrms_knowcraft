# notifications.py
import logging
from typing import Optional, Dict, Any
from .pdf_maker import generate_offer_letter
from .sender import send_email, send_text
from .templates import HTML_TEMPLATES
from .opensign import send_to_opensign_and_get_link
from accounts.models import User
logger = logging.getLogger(__name__)
from django.conf import settings

FRONTEND_URL = getattr(settings,"FRONTEND_URL")

# ----------------------------------------------------------------------
# Mapping: stage → notification configuration
# ----------------------------------------------------------------------

_NOTIFICATION_MAP: dict[str, dict[str, Any]] = {

    # --------------------------------------------------------------
    # 0. APPLICATION / DUPLICATE CHECK
    # --------------------------------------------------------------
    "received": {
        "email": {
            "subject": "Application Received - Thank You",
            "text": "Thank you for applying to Knowcraft Analytics. Your application has been successfully received and is now under review by our HR team.",
        },
        "sms": "Thank you for applying to Knowcraft Analytics. Your application has been received and is under review.",
        "log": "Application acknowledgment sent to {candidate.candidate_email}",
    },
    "duplicate_rejected": {
        "email": {
            "subject": "Duplicate Application Notification",
            "text": "Thank you for your interest in Knowcraft Analytics. We have already received a recent application from you. As per our duplicate application policy, this submission cannot be processed further.",
        },
        "sms": """Dear {candidate.candidate_name},

Thank you for your interest in opportunities with Knowcraft Analytics.

Our records indicate that a recent application has already been received from you. As per our duplicate application policy, we are unable to process this submission further at this time.

You are welcome to apply again after a reasonable period.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        "log": "Duplicate rejection sent to {candidate.candidate_email}",
    },

    # --------------------------------------------------------------
    # 1. SHORTLIST + INTERVIEW FLOW
    # --------------------------------------------------------------
    "shortlisted": {
        "email": {
            "subject": "You Have Been Shortlisted",
            "text": "We are pleased to inform you that your profile has been shortlisted for the next stage of our selection process.",
        },
        "sms": "Congratulations! Your profile has been shortlisted for the next stage at Knowcraft Analytics.",
        "log": "Shortlisting notification sent to {candidate.candidate_email}",
        "schedule_link": True
    },
    "interview_pending_1": {
        "email": {
            "subject": "HR Interview Scheduled",
            "text": "Your HR interview has been scheduled. Please check your email for complete details and joining link.",
        },
        "sms": "Your HR interview has been scheduled. Please check your email for date, time and joining link.",
        "log": "Interview pending notification sent to {candidate.candidate_email}",
    },
    "interview_done_1": {
        "email": {
            "subject": "Thank You for Attending the HR Interview",
            "text": "Thank you for taking the time to attend the HR interview. Our team is currently reviewing all candidates.",
        },
        "sms": "Thank you for attending the HR interview. We will update you shortly on the next steps.",
        "log": "Interview completion message sent to {candidate.candidate_email}",
    },
    "interview_rejected_1": {
        "email": {
            "subject": "HR Interview Outcome",
            "text": "Thank you for your participation in the HR interview. After careful consideration, we will not be moving forward with your application at this time.",
        },
        "sms": """Dear {candidate.candidate_name},

Greetings from Knowcraft Analytics.

Thank you for taking the time to participate in the HR round of our interview process.

After careful consideration, we regret to inform you that we will not be proceeding with your application further at this stage. While we were impressed with your profile, the decision was based on current requirements.

We sincerely appreciate your interest and wish you every success in your future endeavors.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        "log": "Interview round 1 rejection sent to {candidate.candidate_email}",
    },
    "interview_next_2": {
        "email": {
            "subject": "Technical Round Scheduled",
            "text": "You have successfully cleared the HR round and have been shortlisted for the Technical Round.",
        },
        "sms": "You have cleared the HR round and are now shortlisted for the Technical Round.",
        "log": "Round 2 notification sent to {candidate.candidate_email}",
        "schedule_link": True
    },
    "interview_pending_2": {
        "email": {
            "subject": "Technical Interview Scheduled",
            "text": "Your Technical interview has been scheduled. Please check your email for details and joining link.",
        },
        "sms": "Your Technical interview has been scheduled. Please check your email for date, time and link.",
        "log": "Interview round 2 pending notification sent to {candidate.candidate_email}",
    },
    "interview_done_2": {
        "email": {
            "subject": "Thank You for Attending the Technical Interview",
            "text": "Thank you for attending the Technical interview. Our panel is currently evaluating the results.",
        },
        "sms": "Thank you for attending the Technical interview. We will update you soon.",
        "log": "Interview round 2 completion message sent to {candidate.candidate_email}",
    },
    "interview_rejected_2": {
        "email": {
            "subject": "Technical Round Outcome",
            "text": "Thank you for your time and effort in the Technical round. We will not be proceeding further with your application at this stage.",
        },
        "sms": """Dear {candidate.candidate_name},

Greetings from Knowcraft Analytics.

Thank you for participating in the Technical Round of our interview process.

Following a thorough evaluation, we regret to inform you that we will not be moving forward with your application. We truly value the time and effort you invested.

We encourage you to explore future opportunities with us and wish you continued success in your career.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        "log": "Interview rejection for round 2 sent to {candidate.candidate_email}",
    },
    "interview_next_3": {
        "email": {
            "subject": "Case Study Round Scheduled",
            "text": "You have successfully cleared the Technical round and have been shortlisted for the Case Study Round.",
        },
        "sms": "You have cleared the Technical round and are now shortlisted for the Case Study Round.",
        "log": "Round 3 notification sent to {candidate.candidate_email}",
        "schedule_link": True
    },
    "interview_pending_3": {
        "email": {
            "subject": "Case Study Round Scheduled",
            "text": "Your Case Study round has been scheduled. Please check your email for complete details.",
        },
        "sms": "Your Case Study round has been scheduled. Please check your email for details.",
        "log": "Interview round 3 pending notification sent to {candidate.candidate_email}",
    },
    "interview_done_3": {
        "email": {
            "subject": "Thank You for Attending the Case Study Round",
            "text": "Thank you for completing the Case Study round. Our team is now reviewing the submissions.",
        },
        "sms": "Thank you for completing the Case Study round. We will update you shortly.",
        "log": "Interview round 3 completion message sent to {candidate.candidate_email}",
    },
    "interview_rejected_3": {
        "email": {
            "subject": "Case Study Round Outcome",
            "text": """Dear {candidate.candidate_name},

Greetings from Knowcraft Analytics.

Thank you for participating in the Case Study Round of our interview process.

After careful consideration, we regret to inform you that we will not be proceeding further with your application. We sincerely appreciate your effort and interest in our organization.

We wish you the very best for your professional journey ahead.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        },
        "sms": "Thank you for the Case Study round. We will not be moving forward with your application.",
        "log": "Interview rejection for round 3 sent to {candidate.candidate_email}",
    },
    "interview_next_final": {
        "email": {
            "subject": "Final Round Scheduled",
            "text": "You have successfully cleared the Case Study round and have been shortlisted for the Final Round.",
        },
        "sms": "You have cleared the Case Study round and are now shortlisted for the Final Round.",
        "log": "Final Round selection notification sent to {candidate.candidate_email}",
        "schedule_link": True
    },
    "interview_pending_final": {
        "email": {
            "subject": "Final Interview Scheduled",
            "text": "Your Final interview has been scheduled. Please check your email for details and joining link.",
        },
        "sms": "Your Final interview has been scheduled. Please check your email for details.",
        "log": "Final Interview pending notification sent to {candidate.candidate_email}",
    },
    "interview_done_final": {
        "email": {
            "subject": "Thank You for Attending the Final Round",
            "text": "Thank you for attending the Final interview. The panel is now deliberating.",
        },
        "sms": "Thank you for attending the Final round. We will update you soon.",
        "log": "Final Interview completion message sent to {candidate.candidate_email}",
    },
    "interview_rejected_final": {
        "email": {
            "subject": "Final Round Outcome",
            "text": "Thank you for your time and effort throughout the final round. We will not be proceeding with your candidature at this stage.",
        },
        "sms": """Dear {candidate.candidate_name},

Greetings from Knowcraft Analytics.

Thank you for taking the time to participate in the Final Round of our selection process.

After comprehensive evaluation, we regret to inform you that we will not be moving forward with your application. This was a competitive process, and we appreciate your engagement throughout.

We wish you success in all your future endeavors.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        "log": "Interview rejection for final round sent to {candidate.candidate_email}",
    },
    "interview_next_management_client": {
        "email": {
            "subject": "Management / Client Round Scheduled",
            "text": "You have successfully cleared the previous rounds and have been shortlisted for the Management / Client Round.",
        },
        "sms": "You have been shortlisted for the Management / Client Round.",
        "log": "Management Client Round notification sent to {candidate.candidate_email}",
        "schedule_link": True
    },
    "interview_pending_management_client": {
        "email": {
            "subject": "Management / Client Interview Scheduled",
            "text": "Your Management / Client interview has been scheduled. Please check your email for details.",
        },
        "sms": "Your Management / Client interview has been scheduled. Please check your email.",
        "log": "Interview management client round pending notification sent to {candidate.candidate_email}",
    },
    "interview_done_management_client": {
        "email": {
            "subject": "Thank You for Attending the Management / Client Round",
            "text": "Thank you for attending the Management / Client interview. The final decision is under review.",
        },
        "sms": "Thank you for attending the Management / Client round. We will update you shortly.",
        "log": "Interview management client round completion message sent to {candidate.candidate_email}",
    },
    "interview_rejected_management_client": {
        "email": {
            "subject": "Management / Client Round Outcome",
            "text": "Thank you for your participation in the Management / Client round. We regret to inform you that we will not be proceeding further.",
        },
        "sms": """Dear {candidate.candidate_name},

Greetings from Knowcraft Analytics.

Thank you for participating in the Management / Client Round of our interview process.

Following detailed discussions and evaluation, we regret to inform you that we will not be progressing further with your application. We greatly appreciate the time and effort you invested in meeting with our team.

We encourage you to stay connected for future opportunities and wish you continued success.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        "log": "Interview rejection for management client round sent to {candidate.candidate_email}",
    },

    # --------------------------------------------------------------
    # 2. SELECTION & APPROVAL FLOW
    # --------------------------------------------------------------
    "selected": {
        "email": {
            "subject": "You Have Been Selected",
            "text": "Congratulations! You have been selected by the interview panel. Your profile is now with the approval committee.",
        },
        "sms": """Dear {candidate.candidate_name},
Congratulations! 🎉

We are pleased to inform you that you have been selected for the position of *{candidate.job.mrf.designation.name}* at Knowcraft Analytics after successfully completing all interview rounds.

Our team was impressed with your skills and performance, and we look forward to having you onboard.

Our HR team will connect with you shortly to share the offer details and next steps.

Congratulations once again and welcome to Knowcraft Analytics!

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        "log": "Selection notification sent to {candidate.candidate_email}",
    },
    "approval_pending": {
        "email": {
            "subject": "Profile Sent for Final Approval",
            "text": "Your profile has been forwarded for final approval. We will update you as soon as the decision is received.",
        },
        "sms": "Your profile has been sent for final approval. We will keep you posted.",
        "log": "Approval pending notification sent to {candidate.candidate_email}",
    },
    "approved": {
        "email": {
            "subject": "Profile Approved - Next Steps",
            "text": "Your profile has been officially approved. Our HR team will now prepare your offer letter.",
        },
        "sms": "Your profile has been approved. Offer letter preparation has started.",
        "log": "Approval confirmation sent to {candidate.candidate_email}",
    },
    "approval_rejected": {
        "email": {
            "subject": "Application Update",
            "text": "After careful review, the hiring manager has decided not to proceed with your profile at this time.",
        },
        "sms": "We regret to inform you that your profile was not approved at this stage.",
        "log": "Approval rejection sent to {candidate.candidate_email}",
    },

    # ---------------------------- SALARY & ANNEXURE FLOW ----------------------------
    "salary_docs_pending": {
        "email": {
            "subject": "Request to Upload Salary Documents",
            "text": "To proceed with your offer, please upload your latest salary slips and bank statements using the secure link provided.",
        },
        "sms": "Please upload your latest salary slips and bank statements using the link sent to your email.",
        "log": "Salary document upload request sent to {candidate.candidate_email}",
    },
    "salary_docs_uploaded": {
        "email": {
            "subject": "Salary Documents Received",
            "text": "Thank you. We have received your salary documents. Our HR team will review them shortly.",
        },
        "sms": "Salary documents received. HR will review them shortly.",
        "log": "Salary documents uploaded confirmation sent to {candidate.candidate_email}",
    },
    "hr_review_docs": {
        "email": {
            "subject": "Salary Documents Under Review",
            "text": "Your salary documents are currently being reviewed by HR.",
        },
        "sms": "Your salary documents are under HR review.",
        "log": "HR review of salary documents started for {candidate.candidate_email}",
    },
    "hr_review_ok": {
        "email": {
            "subject": "Salary Documents Verified Successfully",
            "text": "Your salary documents have been successfully verified. We are now preparing your salary annexure.",
        },
        "sms": "Salary documents verified. Salary annexure is being prepared.",
        "log": "HR verified salary documents for {candidate.candidate_email}",
    },
    "hr_review_rejected": {
        "email": {
            "subject": "Salary Documents Require Re-upload",
            "text": "Some of the uploaded salary documents were unclear or incomplete. Please re-upload the required files.",
        },
        "sms": "Some salary documents need re-upload. Please check your email for details.",
        "log": "HR rejected salary documents for {candidate.candidate_email}",
    },
    "salary_annexure_prep": {
        "email": {
            "subject": "Salary Annexure Under Preparation",
            "text": "We are preparing your salary annexure based on the verified documents.",
        },
        "sms": "Your salary annexure is being prepared.",
        "log": "Salary annexure preparation started for {candidate.candidate_email}",
    },
    "salary_annexure_review": {
        "email": {
            "subject": "Salary Annexure Sent for Approval",
            "text": "Your salary annexure has been forwarded to the HR Head for final approval.",
        },
        "sms": "Salary annexure sent for HR Head approval.",
        "log": "Salary annexure sent for approval for {candidate.candidate_email}",
    },
    "approved_annexure": {
        "email": {
            "subject": "Salary Annexure Approved",
            "text": "Your salary annexure has been approved. We will now prepare your formal offer letter.",
        },
        "sms": "Salary annexure approved. Offer letter preparation in progress.",
        "log": "Salary annexure approval sent to {candidate.candidate_email}",
    },
    "rejected_annexure": {
        "email": {
            "subject": "Salary Annexure Requires Revision",
            "text": "The HR Head has requested some changes to the salary annexure. We will update and resend it shortly.",
        },
        "sms": "Salary annexure requires revision. We will update you shortly.",
        "log": "Salary annexure rejected for {candidate.candidate_email}",
    },

    # --------------------------------------------------------------
    # 3. OFFER FLOW
    # --------------------------------------------------------------
    "offer_pending": {
        "email": {
            "subject": "Offer Letter Preparation in Progress",
            "text": "Your offer letter is currently being prepared by the HR team.",
        },
        "sms": "Your offer letter is being prepared.",
        "log": "Offer pending notification sent to {candidate.candidate_email}",
    },
    "offer_sent": {
        "email": {
            "subject": "Your Offer Letter - Signature Required",
            "text": "Please review and sign your offer letter using the secure link provided in this email.",
        },
        "sms": "Your offer letter is ready. Please check your email to review and sign.",
        "opensign": True,
        "log": "Offer letter sent for signing to {candidate.candidate_email}",
    },
    "offer_accepted": {
        "email": {
            "subject": "Offer Accepted - Next Steps",
            "text": "Thank you for accepting the offer. Please upload your resignation / relieving letter to proceed with onboarding.",
        },
        "sms": "Offer accepted. Please upload your resignation letter using the link sent to your email.",
        "log": "Offer acceptance notification sent to {candidate.candidate_email}",
    },
    "offer_rejected": {
        "email": {
            "subject": "Offer Declined",
            "text": "We note that you have declined the offer. Your application has been closed. Thank you for considering Knowcraft Analytics.",
        },
        "sms": "You have declined the offer. Your application is now closed.",
        "log": "Offer rejection notification sent to {candidate.candidate_email}",
    },

    # --------------------------------------------------------------
    # 4. RESIGNATION FLOW
    # --------------------------------------------------------------
    "resignation_pending": {
        "email": {
            "subject": "Request to Upload Resignation Letter",
            "text": "To proceed with your joining formalities, please upload your resignation / relieving letter within 48 hours using the secure link.",
        },
        "sms": "Please upload your resignation letter within 48 hours using the link sent to your email.",
        "log": "Resignation letter request sent to {candidate.candidate_email}",
    },
    "resignation_uploaded": {
        "email": {
            "subject": "Resignation Letter Received",
            "text": "Thank you. We have received your resignation letter. HR will verify it shortly.",
        },
        "sms": "Resignation letter received. HR will verify shortly.",
        "log": "Resignation uploaded confirmation sent to {candidate.candidate_email}",
    },
    "resignation_review": {
        "email": {
            "subject": "Resignation Letter Under Review",
            "text": "Your resignation letter is currently under review by HR.",
        },
        "sms": "Your resignation letter is under HR review.",
        "log": "Resignation review started for {candidate.candidate_email}",
    },
    "resignation_approved": {
        "email": {
            "subject": "Resignation Letter Approved",
            "text": "Your resignation letter has been approved. Please proceed with uploading the remaining joining documents.",
        },
        "sms": "Resignation letter approved. Please upload remaining documents.",
        "log": "Resignation approved notification sent to {candidate.candidate_email}",
    },
    "resignation_rejected": {
        "email": {
            "subject": "Resignation Letter Requires Re-upload",
            "text": "Your resignation letter was unclear or incomplete. Please re-upload a clear copy using the same link.",
        },
        "sms": "Resignation letter requires re-upload. Please check your email.",
        "log": "Resignation rejected notification sent to {candidate.candidate_email}",
    },

    # --------------------------------------------------------------
    # 5. DOCUMENT FLOW
    # --------------------------------------------------------------
    "docs_pending": {
        "email": {
            "subject": "Upload Joining Documents",
            "text": "Please upload all required joining documents using the secure link provided.",
        },
        "sms": """Dear {candidate.candidate_name},

Greetings from Knowcraft Analytics!

Congratulations on your selection. We are excited to move forward with your onboarding process.

To proceed, please upload the required documents using the link below:
{FRONTEND_URL}/api/application/documents/upload/{candidate.id}

Documents Required:
1. Certificates and Marksheets till Highest Qualification (Mandatory)
2. Last Organization Documents (if applicable):
   - Offer / Appointment Letter
   - Experience & Relieving Letter
   - Increment Letter
   - Last 3 Months Salary Slips
3. Aadhar Card (Mandatory)
4. PAN Card (Mandatory)
5. Passport Size Photograph (Mandatory)

Kindly upload the documents at the earliest to help us proceed with the next steps.

Feel free to reach out in case of any questions.

Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        "log": "Document upload request sent to {candidate.candidate_email}",
    },
    "docs_uploaded": {
        "email": {
            "subject": "Documents Received Successfully",
            "text": "Thank you. We have received your documents. Our team will verify them shortly.",
        },
        "sms": "Documents received. Verification in progress.",
        "log": "Documents uploaded confirmation sent to {candidate.candidate_email}",
    },
    "review_docs": {
        "email": {
            "subject": "Document Verification in Progress",
            "text": "Your submitted documents are currently under verification by HR.",
        },
        "sms": "Your documents are under verification.",
        "log": "Document review started for {candidate.candidate_email}",
    },
    "docs_unclear": {
        "email": {
            "subject": "Documents Require Re-upload",
            "text": "Some of your uploaded documents were unclear. Please re-upload clear copies using the same link.",
        },
        "sms": """Dear {candidate.candidate_name},

Greetings from Knowcraft Analytics.

Thank you for submitting your documents as part of the recruitment process.

Upon review, we noticed that some of the submitted documents are incomplete or unclear. We kindly request you to re-upload the required documents using the link below:

{FRONTEND_URL}/api/application/documents/upload/{candidate.id}

Please ensure that the files are properly scanned and all information is clearly visible.

If you need any assistance, please feel free to reach out to us.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        "log": "Documents unclear notification sent to {candidate.candidate_email}",
    },
    "docs_incomplete": {
        "email": {
            "subject": "Documents Incomplete",
            "text": "Some required documents were missing or incomplete. Please upload the complete set using the provided link.",
        },
        "sms": """Dear {candidate.candidate_name},

Greetings from Knowcraft Analytics.

Thank you for submitting your documents as part of the recruitment process.

Upon review, we noticed that some of the submitted documents are incomplete or unclear. We kindly request you to re-upload the required documents using the link below:

{FRONTEND_URL}/api/application/documents/upload/{candidate.id}

Please ensure that the files are properly scanned and all information is clearly visible.

If you need any assistance, please feel free to reach out to us.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        "log": "Documents incomplete notification sent to {candidate.candidate_email}",
    },
    "docs_approved": {
        "email": {
            "subject": "Documents Approved",
            "text": "All your documents have been successfully verified. Your joining process will now begin.",
        },
        "sms": "All documents approved. Joining process started.",
        "log": "Documents approved notification sent to {candidate.candidate_email}",
    },

    # --------------------------------------------------------------
    # 6. JOINING FLOW
    # --------------------------------------------------------------
    "joining_pending": {
        "email": {
            "subject": "Joining Formalities Initiated",
            "text": "Your joining formalities have been initiated. HR will share the next steps shortly.",
        },
        "sms": """Dear {candidate.candidate_name},

We are pleased to inform you that your joining process has been initiated.

Our HR team will share further details and next steps with you shortly.

We look forward to welcoming you to Knowcraft Analytics.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        "log": "Joining pending notification sent to {candidate.candidate_email}",
    },
    "joining_poned": {
        "email": {
            "subject": "Joining Date Postponed",
            "text": "Your joining date has been postponed. HR will communicate the revised date shortly.",
        },
        "sms": "Your joining has been postponed. Updated date will be shared soon.",
        "log": "Joining postponed notification sent to {candidate.candidate_email}",
    },
    "joined": {
        "email": {
            "subject": "Welcome to Knowcraft Analytics!",
            "text": "Congratulations! You have successfully joined Knowcraft Analytics. We look forward to your valuable contribution.",
        },
        "sms": "Welcome to Knowcraft Analytics! Congratulations on joining the team.",
        "log": "Joining confirmation sent to {candidate.candidate_email}",
    },

    # --------------------------------------------------------------
    # FINAL
    # --------------------------------------------------------------
    "rejected": {
        "email": {
            "subject": "Application Closed",
            "text": "We thank you for your interest in Knowcraft Analytics. Your application has been closed at this stage.",
        },
        "sms": """Dear {candidate.candidate_name},

Thank you for your interest in opportunities with Knowcraft Analytics.

We regret to inform you that your application has been closed at this stage.

We appreciate the time you invested and wish you success in your future opportunities.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
        "log": "Final rejection sent to {candidate.candidate_email}",
    },
    "candidate_feedback": {
        "email": {
            "subject": "Candidate Experience Feedback - Knowcraft Analytics",
            "text": "Thank you for your time during our recruitment process. We'd love to hear about your experience.",
        },
        "log": "Feedback request sent to {candidate.candidate_email}",
    },
}

def notify_candidate(candidate: Any, stage: str,cc:list, feedback_link: str = None) -> bool:
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
        pending_docs_html = None
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
                    interviewer_email = mrf.interviewer_email_1
                elif stage == "interview_next_2":
                    interviewer_email = mrf.interviewer_email_2
                elif stage == "interview_next_3":
                    interviewer_email = mrf.interviewer_email_3
                elif stage == "interview_next_final":
                    interviewer_email = mrf.interviewer_email_final
                elif stage == "interview_next_management_client":
                    interviewer_email = mrf.interviewer_email_management_client
                interviewer = Interviewer.objects.filter(email=interviewer_email).first()
                if interviewer:
                    interviewer_id = interviewer.id
                else:
                    interviewer_id = None
                schedule_link = (
                        f"{FRONTEND_URL}/api/slots/available/"
                        f"?candidate_id={candidate.id}&interviewer_id={interviewer_id}"
                    )
                email_cfg["text"] = email_cfg["text"].format(schedule_link=schedule_link)
                sms_text.format(schedule_link=schedule_link)
            except Exception as e:
                print(e)
        try:
            html_template = HTML_TEMPLATES[stage]
            # if stage == "salary_docs_pending":
            #     link = f"{FRONTEND_URL}/api/application/documents/upload/salary-bank/{candidate.id}"
            #     email_cfg["text"].format(link=link)
            #     sms_text.format(link=link)
            # if stage == 'docs_pending':
            #     link = f"{FRONTEND_URL}/api/application/documents/upload/docs/{candidate.id}"
            #     email_cfg["text"].format(link=link)
            #     sms_text.format(link=link)
            # if stage == "resignation_pending":
            #     link = f"{FRONTEND_URL}/api/application/documents/upload/resignation/{candidate.id}"
            #     email_cfg["text"].format(link=link)
            #     sms_text.format(link=link)
            # if stage in ['docs_unclear','docs_incomplete','']:
            #     from onboarding.utils.docs_reupload import get_pending_documents
            #     pending_docs = get_pending_documents(candidate.documents)
            #     pending_docs_html = "<ul>" + "".join(f"<li>{doc}</li>" for doc in pending_docs) + "</ul>"
            send_email(
                to=candidate.candidate_email,
                subject=email_cfg["subject"],
                text=email_cfg["text"],
                cc= cc,
                template=html_template.format(
                    candidate=candidate,
                    sign_url=sign_url,
                    schedule_link=schedule_link,
                    feedback_link=feedback_link
                ),
                attachments=attachments,
            )
        except Exception as exc:
            logger.exception("Email failed for %s (stage=%s): %s", candidate.candidate_email, stage, exc)
            success = False

    # ---------- SMS ----------
    
    if sms_text and getattr(candidate, "candidate_phone", None):
        try:
            sms_text = sms_text.format(candidate=candidate,FRONTEND_URL=FRONTEND_URL)
            send_text(candidate.candidate_phone, sms_text)
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
    # "interview_pending_1": {
    #     "receivers": ["interviewer"],
    #     "subject": "Interview Pending",
    #     "body": "The candidate is ready for interview scheduling.",
    #     "sms": "Interview pending for assigned candidate.",
    # },
    # "interview_pending_2": {
    #     "receivers": ["interviewer"],
    #     "subject": "Interview Pending",
    #     "body": "The candidate is ready for interview scheduling.",
    #     "sms": "Interview pending for assigned candidate.",
    # },
    # "interview_pending_3": {
    #     "receivers": ["interviewer"],
    #     "subject": "Interview Pending",
    #     "body": "The candidate is ready for interview scheduling.",
    #     "sms": "Interview pending for assigned candidate.",
    # },
    # "interview_pending_final": {
    #     "receivers": ["interviewer"],
    #     "subject": "Interview Pending",
    #     "body": "The candidate is ready for interview scheduling.",
    #     "sms": "Interview pending for assigned candidate.",
    # },
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
        "receivers": ["hr",'referral'],
        "subject": "Selected for interview",
        "body": "The candidate is ready for interview scheduling.",
        "sms": """Dear HR Team,

The candidate {candidate.candidate_name} has been shortlisted.

Please proceed with the next steps in the hiring process.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "interview_next_2": {
        "receivers": ["interviewer","hr"],
        "subject": "Selected for next round of interview",
        "body": "The candidate is ready for interview scheduling.",
        "sms": """Dear HR Team,

The candidate {candidate.candidate_name} has successfully cleared the HR round.

Please proceed with the next stage of the hiring process.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "interview_next_3": {
        "receivers": ["interviewer","hr"],
        "subject": "Selected for next round of interview",
        "body": "The candidate is ready for interview scheduling.",
        "sms": """Dear HR Team,

The candidate {candidate.candidate_name} has successfully cleared the Technical round.

Please proceed with the next stage.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "interview_next_final": {
        "receivers": ["interviewer","hr"],
        "subject": "Selected for next round of interview",
        "body": "The candidate is ready for interview scheduling.",
        "sms": """Dear HR Team,

The candidate {candidate.candidate_name} has successfully cleared the Case Study round.

Please proceed with the next stage.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "interview_rejected_1": {
        "receivers": ["interviewer",'referral'],
        "subject": "Candidate rejection",
        "body": "The candidate is rejected in First round of interview.",
        "sms": """Dear Team,

The candidate {candidate.candidate_name} has been rejected following the HR interview round.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "interview_rejected_2": {
        "receivers": ["interviewer",'referral'],
        "subject": "Candidate rejection",
        "body": "The candidate is rejected in Second round of interview.",
        "sms": """Dear Team,

The candidate {candidate.candidate_name} has been rejected following the Technical interview round.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "interview_rejected_3": {
        "receivers": ["interviewer",'referral'],
        "subject": "Candidate rejection",
        "body": "The candidate is rejected in Third round of interview.",
        "sms": """Dear Team,

The candidate {candidate.candidate_name} has been rejected following the Case Study interview round.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "interview_rejected_final": {
        "receivers": ["interviewer",'referral'],
        "subject": "Candidate rejection",
        "body": "The candidate is rejected in Fianl round of interview.",
        "sms": """Dear Team,

The candidate {candidate.candidate_name} has been rejected following the Final interview round.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "interview_pending_management_client": {
        "receivers": ["interviewer"],
        "subject": "Interview Pending (Management / Client)",
        "body": "The candidate is ready for management/client interview scheduling.",
        "sms": "Management/client interview pending for assigned candidate.",
    },
    "interview_next_management_client": {
        "receivers": ["interviewer", "hr"],
        "subject": "Selected for Management / Client Interview",
        "body": "The candidate has been selected for the management/client interview round.",
        "sms": """Dear HR Team,

The candidate {candidate.candidate_name} has successfully cleared the Final round.

Please proceed with the next stage.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "interview_rejected_management_client": {
        "receivers": ["interviewer", "referral"],
        "subject": "Candidate Rejected (Management / Client Round)",
        "body": "The candidate is rejected in the management/client interview round.",
        "sms": """Dear Team,

The candidate {candidate.candidate_name} has been rejected following the Management / Client interview round.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "approval_pending": {
        "receivers": ["department_head"],
        "subject": "Approval Required for Candidate",
        "body": "Candidate is pending managerial approval.",
        "sms": "Candidate approval required.",
    },
    "approved": {
        "receivers": ["hr",'referral'],
        "subject": "Candidate Approved",
        "body": "Candidate has been approved. Move to next steps.",
        "sms": "Candidate approved.",
    },
    "approval_rejected": {
        "receivers": ["hr"],
        "subject": "Candidate Approval Rejected",
        "body": "Approval manager has rejected the candidate’s profile.",
        "sms": """Dear HR Team,

The candidate {candidate.candidate_name} was not approved during the approval stage.

Please take the necessary action to close the process.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    # "salary_docs_uploaded": {
    #     "receivers": ["hr"],
    #     "subject": "Salary Documents Uploaded",
    #     "body": "Salary documents have been uploaded. Review required.",
    #     "sms": "Candidate salary documents uploaded.",
    # },
    # "salary_annexure_prep": {
    #     "receivers": ["hr"],
    #     "subject": "Prepare Salary Annexure",
    #     "body": "Start preparing the salary annexure for the candidate.",
    #     "sms": "Prepare salary annexure.",
    # },
    # "salary_annexure_sent": {
    #     "receivers": ["hr_manager"],
    #     "subject": "Salary Annexure Sent for Approval",
    #     "body": "Salary annexure has been sent for managerial approval.",
    #     "sms": "Salary annexure approval pending.",
    # },
    # "approved_annexure": {
    #     "receivers": ["hr"],
    #     "subject": "Salary Annexure Approved",
    #     "body": "Salary annexure has been approved.",
    #     "sms": "Salary annexure approved.",
    # },
    # "rejected_annexure": {
    #     "receivers": ["hr"],
    #     "subject": "Salary Annexure Rejected",
    #     "body": "Salary annexure has been rejected. Further action required.",
    #     "sms": "Salary annexure rejected.",
    # },
    "offer_pending": {
        "receivers": ["hr"],
        "subject": "Offer Letter Pending",
        "body": "Prepare and send the offer letter to the candidate.",
        "sms": "Offer letter preparation pending.",
    },
    "offer_accepted": {
        "receivers": ["hr"],
        "subject": "Offer Accepted by Candidate",
        "body": "Candidate has accepted the offer.",
        "sms": """Dear {reciever_name},

This is to inform you that {candidate.candidate_name} has formally accepted the offer for the position of {candidate.job.mrf.designation.name}.

Please proceed with the next onboarding steps.

Kindly let us know if any additional details are required.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "offer_rejected": {
        "receivers": ["consultancy","hr","hr_manager"],
        "subject": "Offer Rejected",
        "body": "Candidate has rejected the offer.",
        "sms": """Dear {reciever_name},

This is to inform you that {candidate.candidate_name} has declined the offer for the position of {candidate.job.mrf.designation.name}.

Please proceed with the necessary updates and further hiring actions.

Kindly let us know if any additional information is required.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    # "resignation_uploaded": {
    #     "receivers": ["hr"],
    #     "subject": "Resignation Uploaded",
    #     "body": "Candidate's resignation has been uploaded.",
    #     "sms": "Resignation document uploaded.",
    # },
    "docs_uploaded": {
        "receivers": ["hr"],
        "subject": "Documents Uploaded",
        "body": "Candidate has uploaded joining documents.",
        "sms": """Dear {reciever_name},

This is to inform you that the candidate *{candidate.candidate_name}* has successfully uploaded all the required documents.

You may review the documents and proceed with the next steps of evaluation and onboarding.

Please let us know if any additional information is required.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "joining_pending": {
        "receivers": ["hr", "internal_team", "admin", "department_head"],
        "subject": "Joining Pending",
        "body": "Candidate is pending joining. Prepare required steps.",
        "sms": "Candidate joining pending.",
    },
    "joining_poned": {
        "receivers": ["hr", "department_head"],
        "subject": "Joining Postponed",
        "body": "Candidate has postponed the joining date.",
        "sms": """Dear {reciever_name},

This is to inform you that {candidate.candidate_name} has not joined on the scheduled joining date for the position of {candidate.job.mrf.designation.name}.

The joining has been postponed. Kindly review and advise on the next course of action.

Please let us know if any follow-up is required.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "joined": {
        "receivers": ["hr", "internal_team", "admin", "department_head", "consultancy", "referer"],
        "subject": "Candidate Joined",
        "body": "Candidate has joined successfully.",
        "sms": """Dear Team,

We are pleased to inform you that {candidate.candidate_name} has successfully joined the organization.

We wish them a successful journey with Knowcraft Analytics.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
    "duplicate_rejected": {
        "receivers": ["consultancy"],
        "subject": "Duplicate Profile Rejected",
        "body": "Candidate profile rejected due to duplication.",
        "sms": "Duplicate profile rejected.",
    },
    "rejected": {
        "receivers": ["consultancy", "department_head", "hr",'referral'],
        "subject": "Candidate Rejected",
        "body": "Candidate profile has been rejected.",
        "sms": """Dear Team,

The candidate {candidate.candidate_name} has been rejected.

This concludes the hiring process for this profile.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""",
    },
}

def resolve_internal_emails(candidate, receivers: list[str]) -> list[str]:
    emails = set()

    job = getattr(candidate, "job", None)
    if not job:
        logger.error(f"No job linked with candidate {candidate.id}")
        return []

    mrf = getattr(job, "mrf", None)

    def add_email(email):
        if email:
            emails.add(email)

    def add_user(user):
        if user and getattr(user, "email", None):
            emails.add(user.email)

    def add_users(qs):
        for user in qs:
            add_user(user)

    try:

        for role in receivers:

            # =========================
            # HR (MULTI + OLD SUPPORT)
            # =========================
            if role == "hr":
                add_user(getattr(job, "assigned_to_internal_hr", None))

                if hasattr(job, "assigned_internal_hrs"):
                    add_users(job.assigned_internal_hrs.all())

                continue

            # =========================
            # INTERVIEWERS (FIXED)
            # =========================
            if role == "interviewer" and mrf:

            #     status = candidate.status

            #     if status in ["interview_pending_1","interview_done_1","interview_rejected_1","shortlisted"]:
            #         add_email(getattr(mrf, "interviewer_email_1", None))

            #     elif status in ["interview_pending_2","interview_done_2","interview_rejected_2","interview_next_2"]:
            #         # support both field & M2M
            #         add_email(getattr(mrf, "interviewer_email_2", None))
            #         if hasattr(mrf, "technical_interviewers"):
            #             add_users(mrf.technical_interviewers.all())

            #     elif status in ["interview_pending_3","interview_done_3","interview_rejected_3","interview_next_3"]:
            #         add_email(getattr(mrf, "interviewer_email_3", None))

            #     elif status in ["interview_pending_final","interview_done_final","interview_rejected_final","interview_next_final"]:
            #         add_email(getattr(mrf, "interviewer_email_final", None))

            #     elif status in ["interview_pending_management_client","interview_done_management_client","interview_rejected_management_client","interview_next_management_client"]:
            #         add_email(getattr(mrf, "interviewer_email_management_client", None))

                continue

            # =========================
            # CONSULTANCY (MULTI + OLD)
            # =========================
            if role == "consultancy":
                if candidate.source == 'consultancy':
                    add_user(getattr(job, "assigned_to_consultancy", None))

                    if hasattr(job, "assigned_consultancies"):
                        add_users(job.assigned_consultancies.all())

                continue

            # =========================
            # DEPARTMENT HEAD
            # =========================
            if role == 'department_head':
                if mrf:
                    user = getattr(mrf, "requested_by", None)
                    if user and user.role == 'department_head':
                        add_user(user)
                continue

            # =========================
            # HR MANAGER
            # =========================
            if role == 'hr_manager':
                user = getattr(job, "assigned_by", None)
                if user and user.role == 'hr_manager':
                    add_user(user)
                continue

            # =========================
            # ADMIN (FIXED → ALL ADMINS)
            # =========================
            if role == 'admin':
                admins = User.objects.filter(role='admin') \
                    .exclude(email__isnull=True) \
                    .exclude(email="")
                add_users(admins)
                continue

            # =========================
            # REFERRER (FIXED NAME)
            # =========================
            if role == "referrer":
                add_email(getattr(candidate, "referral_email", None))
                continue

            # =========================
            # INTERNAL TEAM (OPTIONAL)
            # =========================
            if role == "internal_team":
                # Future logic
                continue

        return list(emails)

    except Exception as e:
        logger.exception(f"Error finding emails to send: {e}")
        return []

def resolve_internal_phones(candidate, receivers: list[str]) -> list[str]:
    phones = set()

    job = getattr(candidate, "job", None)
    if not job:
        logger.error(f"No job linked with candidate {candidate.id}")
        return []

    mrf = getattr(job, "mrf", None)

    def add_phone(phone):
        if phone:
            phones.add(phone)

    def add_user(user):
        if user and getattr(user, "phone", None):
            phones.add(user.phone)

    def add_users(qs):
        for user in qs:
            add_user(user)

    try:
        for role in receivers:

            # =========================
            # HR (MULTI + OLD)
            # =========================
            if role == "hr":
                add_user(getattr(job, "assigned_to_internal_hr", None))

                if hasattr(job, "assigned_internal_hrs"):
                    add_users(job.assigned_internal_hrs.all())

                continue

            # =========================
            # CONSULTANCY (MULTI + OLD)
            # =========================
            if role == "consultancy":
                if candidate.source == 'consultancy':
                    add_user(getattr(job, "assigned_to_consultancy", None))

                    if hasattr(job, "assigned_consultancies"):
                        add_users(job.assigned_consultancies.all())

                continue

            # =========================
            # DEPARTMENT HEAD
            # =========================
            if role == 'department_head':
                if mrf:
                    user = getattr(mrf, "requested_by", None)
                    if user and user.role == 'department_head':
                        add_user(user)
                continue

            # =========================
            # HR MANAGER
            # =========================
            if role == 'hr_manager':
                user = getattr(job, "assigned_by", None)
                if user and user.role == 'hr_manager':
                    add_user(user)
                continue

            # =========================
            # ADMIN (FIXED)
            # =========================
            if role == 'admin':
                admins = User.objects.filter(role='admin') \
                    .exclude(phone__isnull=True) \
                    .exclude(phone="")
                add_users(admins)
                continue

            # =========================
            # REFERRER (FIXED)
            # =========================
            if role == "referrer":
                add_phone(getattr(candidate, "referral_phone", None))
                continue

        return list(phones)

    except Exception as e:
        logger.exception(f"Error finding phones to send: {e}")
        return []

def notify_internal(candidate: Any, stage: str, cc: list) -> bool:
    recievers = NOTIFY_INTERNAL_MAP[stage]['receivers']
    subject = NOTIFY_INTERNAL_MAP[stage]['subject']
    body = NOTIFY_INTERNAL_MAP[stage]['body']
    base_sms_text = NOTIFY_INTERNAL_MAP[stage]['sms']  # FIX

    if not recievers:
        logger.warning("No notification recievers for stage '%s'", stage)
        return False

    to_emails = resolve_internal_emails(candidate, recievers)
    to_phones = resolve_internal_phones(candidate, recievers)

    if not to_emails:
        logger.warning(f"No internal email recipients found for stage {stage}")
        return False

    try:
        from .templates import NOTIFY_INTERNAL_HTML_TEMPLATES

        template_base = NOTIFY_INTERNAL_HTML_TEMPLATES[stage]

        for email in to_emails:

            feedback_link = ""
            reciever_name = ""

            # =========================
            # FEEDBACK LINK
            # =========================
            if stage.startswith("interview_pending"):

                mapping = {
                    'interview_pending_1': ("hr_round", "hr-feedback-form"),
                    'interview_pending_2': ("technical_round", "technical-feedback-form-one"),
                    'interview_pending_3': ("case_study_round", "technical-feedback-form-two"),
                    'interview_pending_final': ("final_round", "final-feedback-form"),
                    'interview_pending_management_client': ("management_client_round", "management-feedback-form"),
                }

                if stage in mapping:
                    round, endpoint = mapping[stage]
                    feedback_link = f"{FRONTEND_URL}/api/slots/{endpoint}/?interview_round={round}&job_application={candidate.id}"

            # =========================
            # RECEIVER NAME (SAFE)
            # =========================
            reciever_name = email.split("@")[0]  # fallback

            template = template_base.format(
                candidate=candidate,
                feedback_link=feedback_link,
                reciever_name=reciever_name
            )

            send_email(email, subject=subject, text=body, template=template)

        # =========================
        # SMS (FIXED)
        # =========================
        if to_phones:
            for phone in to_phones:
                sms_text = base_sms_text.format(
                    reciever_name="User",
                    candidate=candidate,
                    FRONTEND_URL=FRONTEND_URL
                )
                send_text(to=phone, text=sms_text)

        logger.info(
            f"Internal notification sent for {candidate.candidate_name} at stage '{stage}'"
        )
        return True

    except Exception as e:
        logger.exception(f"Failed internal notification: {e}")
        return False
def trigger_feedback_email(candidate: Any, feedback_type: str):
    """
    Creates/fetches CandidateExperienceFeedback and sends a separate feedback email.
    """
    from dashboard.models import CandidateExperienceFeedback
    
    try:
        # Create or get feedback record
        feedback, created = CandidateExperienceFeedback.objects.get_or_create(
            application=candidate,
            feedback_type=feedback_type,
            defaults={'is_submitted': False}
        )
        
        feedback_link = f"{FRONTEND_URL}/candidate/feedback/{candidate.id}"
        
        logger.info("Triggering separate feedback email for %s (type=%s)", candidate.candidate_email, feedback_type)
        
        # Send the email
        # We pass cc=[] because feedback is usually private to the candidate
        return notify_candidate(candidate, 'candidate_feedback', cc=[], feedback_link=feedback_link)
    except Exception as e:
        logger.exception("Failed to trigger feedback email for %s: %s", candidate.candidate_email, e)
        return False
