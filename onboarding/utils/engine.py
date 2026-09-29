# engine.py
import logging
from .stage_transition_rules import get_auto_next, validate_transition
from .notifications import notify_candidate,notify_internal
from .cc_rules import get_cc_for_stage
logger = logging.getLogger(__name__)
from django.conf import settings

FRONTEND_URL = getattr(settings,"FRONTEND_URL")

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
    "selected",
    # "approved",
    # "approval_rejected",
    # "salary_docs_uploaded",
    # "hr_review_docs",
    # "hr_review_ok",
    # "hr_review_rejected",
    # Salary Annexure
    # "salary_annexure_prep",
    # "salary_annexure_review",
    # "approved_annexure",
    # "rejected_annexure",
    # Offer
    # "offer_pending",
    # "offer_sent",
    # "offer_accepted",
    # "offer_rejected",
    # Documents
    "docs_pending",
    # "docs_uploaded",
    # "review_docs",
    # "docs_approved",
    "docs_incomplete",
    "docs_unclear",
    # Joining
    "joining_pending",
    # "joining_poned",
    # "joined",
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
    # "approved",                # Notify HR
    "approval_rejected",       # Notify HR
    # Salary Annexure Flow
    # "salary_annexure_prep",    # Notify HR to prepare annexure
    # "salary_annexure_review",    # Notify HR manager
    # "approved_annexure",       # Notify HR
    # "rejected_annexure",       # Notify HR
    # Offer Flow (Internal Steps)
    # "offer_pending",           # Notify HR to prepare offer
    "offer_accepted",
    "offer_rejected",
    # Document Verification
    "docs_uploaded",           # HR reviews
    # Joining
    # "joining_pending",         # Notify HR/IT/Admin internally
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


def _notify_hrs_on_joining_pending(job, candidate):
    """Notify assigned HRs with names of other active candidates when one reaches joining_pending."""
    try:
        from onboarding.utils.sender import send_email
        from django.conf import settings

        active_apps = job.applications.filter(is_active=True).exclude(id=candidate.id).exclude(
            status__in=[
                'rejected', 'duplicate_rejected', 'backed_out', "offer_rejected",
                'joined', 'terminated_bgv', 'terminated_misconduct', 'terminated_other',
                "interview_rejected_1", "interview_rejected_2", "interview_rejected_3",
                "interview_rejected_final", "interview_rejected_management_client"
            ]
        )
        if not active_apps.exists():
            return

        active_candidates = []
        for app in active_apps:
            name = app.candidate_name or app.original_filename or f"Candidate {app.id}"
            active_candidates.append(name)

        hr_recipients = []
        if job.assigned_to_internal_hr and job.assigned_to_internal_hr.email:
            hr_recipients.append((job.assigned_to_internal_hr.name or "HR", job.assigned_to_internal_hr.email))
        for hr_user in job.assigned_internal_hrs.all():
            if hr_user.email and (hr_user.name or "HR", hr_user.email) not in hr_recipients:
                hr_recipients.append((hr_user.name or "HR", hr_user.email))

        if not hr_recipients and job.posted_by and job.posted_by.email:
            hr_recipients.append((job.posted_by.name or "HR", job.posted_by.email))

        if not hr_recipients:
            return

        frontend_url = getattr(settings, "FRONTEND_URL", "")
        job_title = job.job_title
        cand_name = candidate.candidate_name or "A candidate"
        count = len(active_candidates)

        names_html = "".join([f"<li style='margin-bottom:6px;'><strong>{name}</strong></li>" for name in active_candidates])
        names_text = "\n".join([f"- {name}" for name in active_candidates])

        for hr_name, hr_email in hr_recipients:
            subject = f"Action Required: Candidate Reached Joining Pending – Update MRF for {job_title}"
            template = f"""
            <html>
            <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
                <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
                    <tr>
                        <td align="center" style="padding:30px 15px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                                <tr>
                                    <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                        <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                                    </td>
                                </tr>
                                <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                                <tr>
                                    <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                        <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:22px;font-weight:600;">Action Required: Update MRF</h2>
                                        <p style="margin:0 0 16px 0;">Dear <strong>{hr_name}</strong>,</p>
                                        <p style="margin:0 0 16px 0;">
                                            Candidate <strong>{cand_name}</strong> has reached the <strong>Joining Pending</strong> stage for 
                                            position <strong>{job_title}</strong>.
                                        </p>
                                        <p style="margin:0 0 12px 0;">
                                            There are currently <strong>{count} other candidate(s)</strong> actively being worked on for this job:
                                        </p>
                                        <div style="background:#f8fafc;padding:14px 20px;border-radius:8px;border-left:4px solid #3b82f6;margin:0 0 18px 0;">
                                            <ul style="margin:0;padding-left:18px;color:#334155;">
                                                {names_html}
                                            </ul>
                                        </div>
                                        <p style="margin:0 0 24px 0;">
                                            Please review and update the MRF (Manpower Requisition Form) or increase vacancies/headcount if additional positions need to be opened so that the active candidate pipeline is aligned.
                                        </p>
                                        <p style="margin:25px 0 30px 0;text-align:center;">
                                            <a href="{frontend_url}" 
                                               style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:8px;font-weight:600;font-size:16px;display:inline-block;">
                                                Review MRF / Job
                                            </a>
                                        </p>
                                        <p style="margin:20px 0 6px 0;color:#555555;">Best Regards,</p>
                                        <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                        <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                        © 2026 Knowcraft Analytics Private Limited • Confidential
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            text = f"""Dear {hr_name},

Candidate {cand_name} has reached the Joining Pending stage for position {job_title}.

There are currently {count} other candidate(s) actively being worked on for this job:
{names_text}

Please review and update the MRF (Manpower Requisition Form) or increase vacancies/headcount if additional positions need to be opened.

Best regards,
Team HR
Knowcraft Analytics Private Limited
"""
            send_email(
                to=hr_email,
                subject=subject,
                template=template,
                text=text,
                event="mrf_update_reminder_joining_pending",
                email_type="internal"
            )
    except Exception as e:
        logger.exception(f"Error in _notify_hrs_on_joining_pending: {e}")

def automation_engine(candidate, old, new, is_jump=False):
    logger.info(f"AUTO: {candidate.candidate_name} {old} → {new}")

    # 1️⃣ Handle Job and MRF Status Updates (Before validation to ensure sync)

    if new == 'joining_pending':
        job = candidate.job
        if job and job.status != 'joining_pending':
            job.status = 'joining_pending'
            job.save(update_fields=['status'])
            if job.mrf and job.mrf.status != 'joining_pending':
                job.mrf.status = 'joining_pending'
                job.mrf.save(update_fields=['status'])
        if job:
            _notify_hrs_on_joining_pending(job, candidate)
    elif new == 'joined':
        job = candidate.job
        if job:
            if job.positions_filled < job.no_of_positions:
                job.positions_filled += 1
            if job.positions_filled >= job.no_of_positions:
                job.status = 'filled'
                if job.mrf and job.mrf.status != 'filled':
                    job.mrf.status = 'filled'
                    job.mrf.save(update_fields=['status'])
            job.save(update_fields=['status', 'positions_filled'])

    # 2️⃣ Validate transition (for notifications and auto-next)
    if not is_jump:
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

    # 4️⃣ Separate Feedback Email (if applicable)
    FEEDBACK_REJECTION_STATES = {
        "interview_rejected_1",
        "interview_rejected_2",
        "interview_rejected_3",
        "interview_rejected_final",
        "interview_rejected_management_client",
        # "approval_rejected",
        # "rejected",
        # "offer_rejected",
    }
    
    if new in FEEDBACK_REJECTION_STATES:
        from .notifications import trigger_feedback_email
        trigger_feedback_email(candidate, 'rejection')
    elif new == "offer_accepted":
        from django.utils import timezone
        candidate.offer_accepted_date = timezone.now().date()
        from .notifications import trigger_feedback_email
        trigger_feedback_email(candidate, 'offer')

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

    PENDING_STATES = [
        "interview_pending_1",
        "interview_pending_2",
        "interview_pending_3",
        "interview_pending_final",
        "interview_pending_management_client",
        ]
    # If leaving a pending state → clear interview details
    if old in PENDING_STATES and new not in PENDING_STATES:
        candidate.interview_link = None
        candidate.interviewer_name = None
        candidate.interview_scheduled_at = None
        candidate.interview_end_at = None
        # candidate.feedback_link = None
        candidate.round_name = None

    # Prevent JobApplication.save() from double-triggering this engine
    candidate._skip_engine_trigger = True
    candidate.save()

    from slots.models import Interviewer
    interviewer_email, interviewer = None, None
    if new == 'shortlisted':
        if candidate.job.mrf.interviewer_email_1:
            interviewer_email = candidate.job.mrf.interviewer_email_1
            candidate.round_name = "hr_round"
        elif candidate.job.mrf.interviewer_email_2:
            interviewer_email = candidate.job.mrf.interviewer_email_2
            candidate.round_name = "technical_round"
        elif candidate.job.mrf.interviewer_email_3:
            interviewer_email = candidate.job.mrf.interviewer_email_3
            candidate.round_name = "case_study_round"
        elif candidate.job.mrf.interviewer_email_final:
            interviewer_email = candidate.job.mrf.interviewer_email_final
            candidate.round_name = "final_round"
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
            f"{FRONTEND_URL}/api/slots/available/?candidate_id={candidate.id}&interviewer_id={interviewer_id}"
        )
        candidate.inperson_link = (
            f"{FRONTEND_URL}/api/inperson/interview/?candidate_id={candidate.id}&interviewer_id={interviewer_id}"
        )
    else:
        candidate.slot_link = ""
        candidate.inperson_link = ""

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
