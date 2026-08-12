# views.py
from onboarding.utils import docs_reupload
from django.db.models import FileField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.db.models import Q
from .models import JobApplicationDocument,ApprovalNote,SalaryAnnexure,SalaryAnnexureHistory,SalaryComponent,EmailLog, OnboardingTask, OnboardingTaskList, DocumentEsignTask
from onboarding.utils.engine import automation_engine
from .utils.sender import send_email,send_text,send_document
from .serializers import JobApplicationDocumentSerializer,SalaryAnnexureSerializer,SalaryAnnexureHistorySerializer,EmailLogSerializer, OnboardingTaskSerializer, OnboardingTaskListSerializer, DocumentEsignTaskSerializer
import logging
from jobs.models import JobApplication, Job
from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet

from .utils.annexure_history import log_salary_annexure_history
from .utils.send_annexure import send_salary_annexure_email
from accounts.models import User
from django.conf import settings
from dateutil import parser
from django.utils import timezone
logger = logging.getLogger(__name__)

FRONTEND_URL = getattr(settings,"FRONTEND_URL")

class UpdatestatusAPI(APIView):
    permission_classes = [permissions.AllowAny] 
    def post(self, request, id):

        new_status = request.data.get("status") or request.POST.get("status")
        rejection_reason = request.data.get("rejection_reason") or request.POST.get("rejection_reason") or ""

        try:
            application = JobApplication.objects.get(id=id)
        except JobApplication.DoesNotExist:
            return Response({"error": "Job Application not found"}, status=404)

        old_status = application.status

        logger.info(f"[status] {application.candidate_name}: {old_status} → {new_status}")

        ok,reason = automation_engine(application, old_status, new_status)
        if ok:
            from slots.models import Interviewer
            interviewer_email,interviewer = None,None
            if application.status == 'shortlisted':
                if application.job.mrf.interviewer_email_1:
                    interviewer_email = application.job.mrf.interviewer_email_1
                elif application.job.mrf.interviewer_email_2:
                    interviewer_email = application.job.mrf.interviewer_email_2
                elif application.job.mrf.interviewer_email_3:
                    interviewer_email = application.job.mrf.interviewer_email_3
                elif application.job.mrf.interviewer_email_final:
                    interviewer_email = application.job.mrf.interviewer_email_final
            elif application.status == "interview_next_2":
                interviewer_email = application.job.mrf.interviewer_email_2
            elif application.status == "interview_next_3":
                interviewer_email = application.job.mrf.interviewer_email_3
            elif application.status == "interview_next_final":
                interviewer_email = application.job.mrf.interviewer_email_final
            elif application.status == "interview_next_management_client":
                interviewer_email = application.job.mrf.interviewer_email_management_client
            if interviewer_email:
                # interviewer = Interviewer.objects.filter(email=interviewer_email).first()
                name = interviewer_email.split("@")[0].replace(".", " ").title()
                # Ensure interviewer exists → auto-create if not found
                interviewer, created = Interviewer.objects.get_or_create(
                    email=interviewer_email,
                    defaults={"name": name}
                )
            if interviewer:
                interviewer_id = interviewer.id
                application.slot_link = f"{FRONTEND_URL}/api/slots/available/?candidate_id={application.id}&interviewer_id={interviewer_id}"
                application.inperson_link = f"{FRONTEND_URL}/api/inperson/interview/?candidate_id={application.id}&interviewer_id={interviewer_id}"
            else:
                interviewer_id = None
                application.slot_link = ""
                application.inperson_link = ""
            if application.status in ["rejected", "backed_out"] and rejection_reason:
                application.rejection_reason = rejection_reason
            application.save()
            return Response({"success": ok,"status":application.status})
        else:
            return Response({"error": reason}, status=400)

class RevertRejectionAPI(APIView):
    permission_classes = [permissions.AllowAny] 
    def post(self, request, id):
        try:
            application = JobApplication.objects.get(id=id)
        except JobApplication.DoesNotExist:
            return Response({"error": "Job Application not found"}, status=404)

        old_status = application.status
        
        # We only allow reverting from terminal rejection states
        from onboarding.utils.stage_transition_rules import ALLOWED_TRANSITIONS
        
        rejection_states = [
            "duplicate_rejected", "interview_rejected_1", "interview_rejected_2", 
            "interview_rejected_3", "interview_rejected_final", 
            "interview_rejected_management_client", "approval_rejected", 
            "offer_rejected", "rejected"
        ]
        
        if old_status not in rejection_states:
            return Response({"error": f"Candidate is in '{old_status}', which is not a revertible rejected state."}, status=400)
        
        allowed_next = ALLOWED_TRANSITIONS.get(old_status, [])
        if not allowed_next:
            return Response({"error": f"No revert status defined for '{old_status}'."}, status=400)
            
        # ── Smart next-round detection ────────────────────────────────────────
        # For interview rejections, determine the correct next stage by checking
        # which rounds are actually configured in the MRF (i.e. have an interviewer).
        mrf = application.job.mrf
        new_status = allowed_next[0]  # safe default

        if old_status == "interview_rejected_1":
            # Rejected after HR round → try Technical, then Case Study, then Final
            if mrf.interviewer_email_2:
                new_status = "interview_next_2"
            elif mrf.interviewer_email_3:
                new_status = "interview_next_3"
            elif mrf.interviewer_email_final:
                new_status = "interview_next_final"
            else:
                new_status = "selected"

        elif old_status == "interview_rejected_2":
            # Rejected after Technical round → check Case Study, then Final
            if mrf.interviewer_email_3:
                new_status = "interview_next_3"        # case study is configured
            elif mrf.interviewer_email_final:
                new_status = "interview_next_final"    # skip straight to final
            else:
                new_status = "selected"

        elif old_status == "interview_rejected_3":
            # Rejected after Case Study round → check Final round
            if mrf.interviewer_email_final:
                new_status = "interview_next_final"
            else:
                new_status = "selected"

        elif old_status in ("interview_rejected_final", "interview_rejected_management_client"):
            # No further interview round after Final / Management-Client
            new_status = "selected"
        # ─────────────────────────────────────────────────────────────────────

        logger.info(f"[Revert Rejection] {application.candidate_name}: {old_status} → {new_status}")

        ok, reason = automation_engine(application, old_status, new_status)
        if ok:
            from slots.models import Interviewer
            interviewer_email, interviewer = None, None

            # Resolve the interviewer for the new stage
            stage_email_map = {
                "shortlisted":                      (mrf.interviewer_email_1 or mrf.interviewer_email_2
                                                     or mrf.interviewer_email_3 or mrf.interviewer_email_final),
                "interview_next_2":                 mrf.interviewer_email_2,
                "interview_next_3":                 mrf.interviewer_email_3,
                "interview_next_final":             mrf.interviewer_email_final,
                "interview_next_management_client": mrf.interviewer_email_management_client,
            }
            interviewer_email = stage_email_map.get(application.status)

            if interviewer_email:
                name = interviewer_email.split("@")[0].replace(".", " ").title()
                interviewer, _ = Interviewer.objects.get_or_create(
                    email=interviewer_email,
                    defaults={"name": name}
                )
            if interviewer:
                interviewer_id = interviewer.id
                application.slot_link = (
                    f"{FRONTEND_URL}/api/slots/available/"
                    f"?candidate_id={application.id}&interviewer_id={interviewer_id}"
                )
                application.inperson_link = (
                    f"{FRONTEND_URL}/api/inperson/interview/"
                    f"?candidate_id={application.id}&interviewer_id={interviewer_id}"
                )
            else:
                application.slot_link = ""
                application.inperson_link = ""
            application.save()
            return Response({
                "success": ok,
                "status": application.status,
                "slot_link": application.slot_link or None,
                "inperson_link": application.inperson_link or None,
                "book_interview_link": application.slot_link or None,
            })
        else:
            return Response({"error": reason}, status=400)


# class JobCreateAPIView(APIView):
#     permission_classes = [permissions.AllowAny] 
#     def post(self, request):
#         serializer = JobCreateSerializer(data=request.data)
        
#         if serializer.is_valid():
#             job = serializer.save()
#             return Response({
#                 "status": True,
#                 "message": "Job created successfully",
#                 "data": serializer.data
#             }, status=status.HTTP_201_CREATED)
        
#         return Response({
#             "status": False,
#             "errors": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
    
# class CreateCandidateAPIView(APIView):
#     permission_classes = [permissions.AllowAny] 
#     def post(self, request):
#         serializer = CandidateSerializer(data=request.data)
#         if serializer.is_valid():
#             candidate = serializer.save()
#             return Response({
#                 "success": True,
#                 "message": "Candidate created successfully",
#                 "data": CandidateSerializer(candidate).data
#             }, status=status.HTTP_201_CREATED)
#         return Response({
#             "success": False,
#             "errors": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
def is_section_complete(docs, section):
    """
    Section is complete if status == approved
    """
    return getattr(docs, f"{section}_status") == "approved"

def is_section_unclear(docs, section):
    """
    Section is unclear if status == unclear
    """
    return getattr(docs, f"{section}_status") == "unclear"

def is_section_incomplete(docs, section):
    """
    Section is incomplete if status == incomplete
    """
    return getattr(docs, f"{section}_status") == "incomplete"


REQUIRED_SECTIONS = {
    "salary_docs": ["salary"],
    "resignation_docs": ["resignation"],
    "joining_docs": ["personal", "education", "experience"],
}

def evaluate_documents(application):
    docs = application.documents

    # # Salary stage
    # if application.status in ["salary_docs_uploaded","hr_review_docs","salary_docs_unclear","salary_docs_incomplete"]:
    #     if is_section_unclear(docs,"salary"):
    #         automation_engine(application, application.status, "salary_docs_unclear")
    #     elif is_section_incomplete(docs,"salary"):
    #         automation_engine(application, application.status, "salary_docs_incomplete")
    #     elif is_section_complete(docs, "salary"):
    #         automation_engine(application, application.status, "hr_review_ok")

    # # Resignation stage
    # elif application.status in ["resignation_uploaded","resignation_review","resignation_incomplete","resignation_unclear"]:
    #     if is_section_unclear(docs,"resignation"):
    #         automation_engine(application, application.status, "resignation_unclear")
    #     elif is_section_incomplete(docs,"resignation"):
    #         automation_engine(application, application.status, "resignation_incomplete")
    #     elif is_section_complete(docs, "resignation"):
    #         automation_engine(application, application.status, "resignation_approved")

    # Joining documents stage
    if application.status in ["docs_uploaded","review_docs","docs_unclear","docs_incomplete"]:
        if is_section_incomplete(docs, "joining_docs"):
            ok,reason = automation_engine(application, application.status, "docs_incomplete")
            if not ok:
                print(reason)
        elif is_section_unclear(docs, "joining_docs"):
            ok,reason = automation_engine(application, application.status, "docs_unclear")
            if not ok:
                print(reason)
        elif is_section_complete(docs, "joining_docs"):
            docs.document_approved_at = timezone.now()
            docs.save()
            ok,reason = automation_engine(application, application.status, "docs_approved")
            if not ok:
                print(reason)
    elif application.status == "salary_annexure_review" and getattr(docs,'joining_docs_status') == 'approved':
            docs.annexure_approved_at = timezone.now()
            docs.save()
            automation_engine(application, application.status, "approved_annexure")
    elif application.status == "salary_annexure_review" and getattr(docs,'joining_docs_status') not in  ['approved','pending']:
            docs.annexure_rejection_at = timezone.now()
            docs.save()
            automation_engine(application, application.status, "rejected_annexure")

class UploadJobApplicationDocumentAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        application = get_object_or_404(JobApplication, id=id)

        docs, _ = JobApplicationDocument.objects.get_or_create(
            job_application=application
        )

        response_data = JobApplicationDocumentSerializer(docs).data

        # ✅ Add section evaluation flags
        # response_data["salary_complete"] = is_section_complete(docs, "salary")
        # response_data["salary_unclear"] = is_section_unclear(docs, "salary")
        # response_data["salary_incomplete"] = is_section_incomplete(docs, "salary")

        # response_data["resignation_complete"] = is_section_complete(docs, "resignation")
        # response_data["resignation_unclear"] = is_section_unclear(docs, "resignation")
        # response_data["resignation_incomplete"] = is_section_incomplete(docs, "resignation")

        response_data["joining_docs_complete"] = is_section_complete(docs, "joining_docs")
        response_data["joining_docs_unclear"] = is_section_unclear(docs, "joining_docs")
        response_data["joining_docs_incomplete"] = is_section_incomplete(docs, "joining_docs")
        response_data['candidate_name'] = docs.job_application.candidate_name

        return Response(response_data, status=200)

    def post(self, request, id):
        application = get_object_or_404(JobApplication, id=id)

        docs, _ = JobApplicationDocument.objects.get_or_create(
            job_application=application
        )


        # SECTION_FIELDS = {
        #     "salary": ["salary_slip_1", "salary_slip_2", "salary_slip_3", "bank_statement"],
        #     "joining_docs": {
        #     "personal": ["aadhaar", "pan", "passport", "photograph", "address_proof"],
        #     "education": [
        #         "tenth_certificate",
        #         "twelfth_certificate",
        #         "graduation_certificate",
        #         "post_graduation_certificate",
        #     ],
        #     "experience": [
        #         "experience_letter_1",
        #         "experience_letter_2",
        #         "relieving_letter",
        #     ]},
        #     "resignation": ["resignation_letter", "resignation_acceptance"],
        # }

        # for section, fields in SECTION_FIELDS.items():
        #     if getattr(docs, f"{section}_status") == "approved":
        #         for field in fields:
        #             if field in request.FILES:
        #                 return Response(
        #                     {"error": f"{section} documents already approved"},
        #                     status=400
        #                 )
        if getattr(docs,'joining_docs_status') == 'approved' and docs.created_offer_letter:
            return Response(
                {"error": f"Documents already approved!"},
                status=400
            )

        # ✅ File size validation (max 5MB to match FILE_UPLOAD_MAX_MEMORY_SIZE in settings)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
        for field_name, file_obj in request.FILES.items():
            if file_obj.size > MAX_FILE_SIZE:
                return Response(
                    {
                        "error": f"File '{file_obj.name}' exceeds maximum allowed size of 5MB. "
                        "Please upload a smaller file."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 🟢 Save uploaded files
        updated = False
        for field in request.FILES:
            approved_field = f"{field}_approved"
            if hasattr(docs, field):
                # Skip file if it's already approved
                if hasattr(docs, approved_field) and getattr(docs, approved_field) and field != "salary_annexure":
                    continue
                setattr(docs, field, request.FILES[field])
                updated = True

        if not updated:
            return Response({"error": "Invalid document field"}, status=400)
        # else:
        #     if docs.job_application.job.assigned_to_internal_hr:
        #         reciever_name = docs.job_application.job.assigned_to_internal_hr.name
        #         reciever_email = docs.job_application.job.assigned_to_internal_hr.email
        #         candidate_name = docs.job_application.candidate_name
        #         template = f"""<html>
        #             <body style="font-family: Arial, sans-serif; color:#333;">
        #             <p>Hi {reciever_name},</p>
        #             <p>This is to inform you that the candidate <b>{candidate_name}</b> has re-uploaded the documents.</p>
        #             <p>You may review documents and proceed with the next steps of evaluation and onboarding.</p>
        #             <p>Please let me know if any additional information is needed.</p>
        #             <p>Review:<a href='{FRONTEND_URL}/onboarding/documents/{docs.job_application.id}'>Review Documents</a></p>
        #             <br>
        #             <p>Warm regards,<br>
        #             Team - HR <br>
        #             Knowcraft Analytics Private Limited</p>
        #             </body>
        #             </html>
        #             """
        #         send_email(to=reciever_email,template=template,subject='Documents Re-uploaded')

        docs.save()

        # if application.status == "salary_docs_pending":
        #     automation_engine(application, "salary_docs_pending", "salary_docs_uploaded")

        # elif application.status == "resignation_pending":
        #     automation_engine(application, "resignation_pending", "resignation_uploaded")

        if application.status == "docs_pending":
            automation_engine(application, "docs_pending", "docs_uploaded")

        docs.reupload_docuemnts = ''
        docs.reupload_docuemnts_list = []
        docs.save()

        return Response(
            {
                "message": "Documents uploaded successfully",
                "documents": JobApplicationDocumentSerializer(docs).data,
            },
            status=200
        )

class ReviewJobApplicationDocumentsAPI(APIView):

    def get_permissions(self):
        # if self.request.method == "POST":
        #     return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get(self, request, id):
        docs = JobApplicationDocument.objects.filter(
            job_application_id=id
        ).first()

        if not docs:
            return Response([], status=200)

        data = JobApplicationDocumentSerializer(docs).data

        # Add human-readable status display
        # data["salary_status_display"] = docs.get_salary_status_display()
        # data["resignation_status_display"] = docs.get_resignation_status_display()
        data["joining_docs_status_display"] = docs.get_joining_docs_status_display()
        data['candidate_name'] = docs.job_application.candidate_name

        return Response(data, status=200)

    def post(self, request, id):
        docs = get_object_or_404(
            JobApplicationDocument,
            job_application_id=id
        )

        # section = request.data.get("section")
        status_value = request.data.get("status")
        remarks = request.data.get("remarks")

        # if section not in [
        #     "salary", "personal", "education", "experience", "resignation","joining_docs"
        # ]:
        #     return Response({"error": "Invalid section"}, status=400)

        # 🔒 Lock rule
        if getattr(docs, "joining_docs_status") == "approved":
            return Response(
                {"error": f"Documents already approved!"},
                status=400
            )

        setattr(docs, f"joining_docs_status", status_value)
        setattr(docs, f"joining_docs_remarks", remarks)

        updates = request.data.get("documents", {})

        if not updates:
            return Response({"error": "No document review data provided"}, status=400)

        for field, approved in updates.items():
            approved_field = f"{field}_approved"
            if hasattr(docs, approved_field):
                setattr(docs, approved_field, bool(approved))

                # 🔹 Remove file if not approved
                if not approved and hasattr(docs, field):
                    file_field = getattr(docs, field)
                    if file_field:
                        file_field.delete(save=False)  # deletes from storage
                        setattr(docs, field, None)

        docs.save()

        from onboarding.utils.docs_reupload import get_pending_documents
        pending_docs,reupload_docuemnts_list = get_pending_documents(docs)
        docs.reupload_docuemnts = ' '.join(pending_docs)
        docs.reupload_docuemnts_list = reupload_docuemnts_list

        if docs.joining_docs_status == 'approved':
            docs.reupload_docuemnts = ''
            docs.reupload_docuemnts_list = [] 
        docs.save()

        # 🔁 Evaluate partial approval logic
        evaluate_documents(docs.job_application)

        return Response({
            "message": f"Documents has been updated!",
            "status": status_value,
            "documents": JobApplicationDocumentSerializer(docs).data
        })

from decimal import Decimal
from datetime import date, datetime
from uuid import UUID

def make_json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value

class SendApprovalNoteAPIView(APIView):
    """
    Sends approval note email to manager for candidate hiring
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role in ["hr_manager", "admin"]:
            # See all approval notes
            approval_notes = ApprovalNote.objects.all()

        elif user.role == "hr":
            # HR sees only notes created by them
            approval_notes = ApprovalNote.objects.filter(Q(created_by=user) | Q(candidate__job__assigned_internal_hrs=user))

        else:
            # Default: manager sees notes assigned to them
            approval_notes = ApprovalNote.objects.filter(manager=user)

        # Apply privacy filter
        # Admins and HR managers can see ALL records (including private ones)
        if user.role not in ['admin', 'hr_manager']:
            approval_notes = approval_notes.filter(
                Q(candidate__job__is_private=False) |
                Q(candidate__job__is_private=True, candidate__job__posted_by=user) |
                Q(candidate__job__is_private=True, candidate__job__selected_viewers=user) |
                Q(candidate__job__is_private=True, candidate__job__assigned_to_consultancy=user) |
                Q(candidate__job__is_private=True, candidate__job__assigned_to_internal_hr=user) |
                Q(candidate__job__is_private=True, candidate__job__assigned_internal_hrs=user) |
                Q(candidate__job__is_private=True, candidate__job__assigned_consultancies=user)
            )


        candidate_id = request.query_params.get("candidate_id")
        if candidate_id:
            approval_notes = approval_notes.filter(candidate_id=candidate_id)

        approver_id = request.query_params.get("approver_id")
        if approver_id:
            approval_notes = approval_notes.filter(manager_id=approver_id)

        note_status = request.query_params.get("status")
        if note_status:
            approval_notes = approval_notes.filter(status=note_status)

        date_from = request.query_params.get("date_from")
        if date_from:
            approval_notes = approval_notes.filter(created_at__date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            approval_notes = approval_notes.filter(created_at__date__lte=date_to)

        search = request.query_params.get("search")
        if search:
            approval_notes = approval_notes.filter(
                Q(candidate__candidate_name__icontains=search) |
                Q(candidate__job__title__icontains=search) |
                Q(candidate__candidate_email__icontains=search) |
                Q(candidate__job__department__name__icontains=search) |
                Q(candidate__job__designation__name__icontains=search) |
                Q(manager__name__icontains=search) |
                Q(manager__email__icontains=search) |
                Q(created_by__name__icontains=search) |
                Q(created_by__email__icontains=search)
            )

        approval_notes = approval_notes.select_related("candidate").distinct()

        results = []

        for note in approval_notes:
            can_approve = (
                note.manager == request.user
                and note.status == "approval_pending"
            )

            results.append({
                "approval_note_id": str(note.id),
                "candidate_id": str(note.candidate.id),
                "candidate_name": str(note.candidate.candidate_name),
                "can_approve": can_approve,
                "approver_id": str(note.manager.id),
                "status": note.status,
                "bgv_status":note.candidate.bgv_status,
                "bgv_status_display":note.candidate.get_bgv_status_display(),
                "status_display": note.get_status_display(),
                "joining_date": note.candidate.joining_date,
                "created_at": note.created_at,
                "data": note.payload,
                "is_private": note.candidate.job.is_private,
                "document_upload_link": f"{FRONTEND_URL}/api/application/documents/upload/{note.candidate.id}",
                "candidate_experience_link": f"{FRONTEND_URL}/candidate/feedback/{note.candidate.id}",
                "salary_annexure_upload_link": f"{FRONTEND_URL}/upload-salary-annexure/{note.candidate.id}",
                "offer_letter_upload_link": f"{FRONTEND_URL}/review-documents/{note.candidate.id}"
            })

        return Response(
            {
                "count": len(results),
                "approval_notes": results
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        data = request.data  # DRF parses JSON automatically

        # --- Fetch candidate ---
        candidate = get_object_or_404(
            JobApplication,
            id=data.get("candidate_id")
        )
        approver = get_object_or_404(User,id = data.get("approver_id"))
        # --- Resolve relations ---
        mrf = candidate.job.mrf
        department = mrf.department
        designation = mrf.designation
        approver = approver or mrf.requested_by
        requested_by_name = request.user.name
        requested_by_email = request.user.email
        requested_by_role = request.user.role

        # --- HTML Template ---
        html_content = """
        <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:700px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Logo -->
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <!-- Separator -->
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <h2 style="margin:0 0 24px 0;color:#1f2937;font-size:26px;font-weight:600;">Approval Required – Candidate Hiring</h2>
                                
                                <p style="margin:0 0 18px 0;">Dear <strong>{{ approver_name }}</strong>,</p>
                                
                                <p style="margin:0 0 24px 0;">
                                    Sharing the formal approval note regarding <strong>{{ candidate_name }}</strong> shortlisted as 
                                    <strong>{{ designation }}</strong> – <strong>{{ department }}</strong>.
                                </p>
                                
                                <!-- Candidate Details Table -->
                                <h3 style="margin:28px 0 12px 0;color:#1f2937;font-size:18px;font-weight:600;">Candidate Details</h3>
                                <table border="1" cellpadding="12" cellspacing="0" width="100%" style="border-collapse:collapse;border-color:#e2e8f0;font-size:15px;">
                                    <tr style="background:#f8fafc;">
                                        <td style="width:38%;font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Name of Candidate</td>
                                        <td style="border:1px solid #e2e8f0;">{{ candidate_name }}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Designation</td>
                                        <td style="border:1px solid #e2e8f0;">{{ designation }}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Experience</td>
                                        <td style="border:1px solid #e2e8f0;">{{ experience }}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Qualification</td>
                                        <td style="border:1px solid #e2e8f0;">{{ qualification }}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Last Organization</td>
                                        <td style="border:1px solid #e2e8f0;">{{ last_organization }}</td>
                                    </tr>
                                </table>
                                
                                <!-- Interview Rounds -->
                                <h3 style="margin:32px 0 12px 0;color:#1f2937;font-size:18px;font-weight:600;">Interview Rounds</h3>
                                <table border="1" cellpadding="12" cellspacing="0" width="100%" style="border-collapse:collapse;border-color:#e2e8f0;font-size:15px;">
                                    <tr style="background:#f8fafc;">
                                        <td colspan="2" style="font-weight:700;color:#1f2937;border:1px solid #e2e8f0;text-align:center;">Interviewers</td>
                                    </tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">HR Round</td><td style="border:1px solid #e2e8f0;">{{ hr_round_interviewer }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Technical Round</td><td style="border:1px solid #e2e8f0;">{{ tech_round_interviewer }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Case Study Round</td><td style="border:1px solid #e2e8f0;">{{ case_study_round_interviewer }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Final Round</td><td style="border:1px solid #e2e8f0;">{{ final_round_interviewer }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Management / Client Round</td><td style="border:1px solid #e2e8f0;">{{ management_client_round_interviewer }}</td></tr>
                                    
                                    <tr style="background:#f8fafc;">
                                        <td colspan="2" style="font-weight:700;color:#1f2937;border:1px solid #e2e8f0;text-align:center;">Scores</td>
                                    </tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">HR Round</td><td style="border:1px solid #e2e8f0;">{{ hr_round_score }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Technical Round</td><td style="border:1px solid #e2e8f0;">{{ tech_round_score }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Case Study Round</td><td style="border:1px solid #e2e8f0;">{{ case_study_round_score }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Final Round</td><td style="border:1px solid #e2e8f0;">{{ final_round_score }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Management / Client Round</td><td style="border:1px solid #e2e8f0;">{{ management_client_round_score }}</td></tr>
                                </table>
                                
                                <!-- Offer & Other Details -->
                                <h3 style="margin:32px 0 12px 0;color:#1f2937;font-size:18px;font-weight:600;">Offer & Other Details</h3>
                                <table border="1" cellpadding="12" cellspacing="0" width="100%" style="border-collapse:collapse;border-color:#e2e8f0;font-size:15px;">
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Current / Last Drawn CTC</td><td style="border:1px solid #e2e8f0;">{{ current_ctc }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Expected CTC</td><td style="border:1px solid #e2e8f0;">{{ expected_ctc }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">CTC to be Offered</td><td style="border:1px solid #e2e8f0;font-weight:500;">{{ offered_ctc }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Notice Period</td><td style="border:1px solid #e2e8f0;">{{ notice_period }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Office Location</td><td style="border:1px solid #e2e8f0;">{{ office_location }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Source</td><td style="border:1px solid #e2e8f0;">{{ source }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">MRF</td><td style="border:1px solid #e2e8f0;">{{ mrf }}</td></tr>
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">New / Replacement</td><td style="border:1px solid #e2e8f0;">{{ hiring_type }}</td></tr>
                                    {% if remarks %}
                                    <tr><td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Remarks</td><td style="border:1px solid #e2e8f0;">{{ remarks }}</td></tr>
                                    {% endif %}
                                </table>
                                
                                <!-- Action -->
                                <p style="margin:32px 0 8px 0;">
                                    Request you to review the details and share your feedback, if any.
                                </p>
                                <p style="margin:0 0 30px 0;text-align:center;">
                                    <a href="{{FRONTEND_URL}}/onboarding" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:8px;font-weight:600;font-size:16px;display:inline-block;">
                                        View Candidate Profile
                                    </a>
                                </p>
                                
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
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

        # --- Context ---
        context = {
            "approver_name": approver.name,
            "approver_email": approver.email,
            "requested_by_name": requested_by_name,
            "requested_by_email":requested_by_email,
            "requested_by_role":requested_by_role,

            "candidate_name": candidate.candidate_name,
            "candidate_resume_link":candidate.resume.url,
            "designation": designation.name,
            "department": department.name,

            "experience": data.get("experience") or candidate.experience_years,
            "qualification": data.get("qualification"),
            "last_organization": data.get("last_organization"),

            "hr_round_interviewer": data.get("hr_round_interviewer"),
            "tech_round_interviewer": data.get("tech_round_interviewer"),
            "case_study_round_interviewer": data.get("case_study_round_interviewer"),
            "final_round_interviewer": data.get("final_round_interviewer"),
            "management_client_round_interviewer": data.get("management_client_round_interviewer"),

            "hr_round_score": data.get("hr_round_score"),
            "tech_round_score": data.get("tech_round_score"),
            "case_study_round_score": data.get("case_study_round_score"),
            "final_round_score": data.get("final_round_score"),
            "management_client_round_score": data.get("management_client_round_score"),

            "current_ctc": data.get("current_ctc"),
            "expected_ctc": data.get("expected_ctc"),
            "offered_ctc": data.get("offered_ctc"),

            "notice_period": data.get("notice_period"),
            "office_location": data.get("office_location") or candidate.job.mrf.location,

            "source": data.get("source") or candidate.source,
            "mrf": mrf.mrf_name,
            "hiring_type": data.get("hiring_type"),

            "remarks": data.get("remarks"),
            "joining_date": data.get("joining_date"),
            "FRONTEND_URL": getattr(settings,'FRONTEND_URL','https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net')
        }

        # --- Render email ---
        template = Template(html_content)
        html_rendered = template.render(Context(context))
        whatsapp_text = f"""
*Approval Required – Candidate Hiring*

Dear {context.get('approver_name')},

Sharing the formal approval note regarding the candidate shortlisted.

━━━━━━━━━━━━━━━━━━
*Candidate Details*
━━━━━━━━━━━━━━━━━━
Name: {context.get('candidate_name')}
Designation: {context.get('designation')} – {context.get('department')}
Experience: {context.get('experience')}
Qualification: {context.get('qualification')}
Last Organization: {context.get('last_organization')}

━━━━━━━━━━━━━━━━━━
*Interview Rounds – Interviewers*
━━━━━━━━━━━━━━━━━━
HR Round: {context.get('hr_round_interviewer')}
Technical Round: {context.get('tech_round_interviewer')}
Case Study Round: {context.get('case_study_round_interviewer')}
Final Round: {context.get('final_round_interviewer')}
Management / Client Round: {context.get('management_client_round_interviewer')}

━━━━━━━━━━━━━━━━━━
*Interview Scores*
━━━━━━━━━━━━━━━━━━
HR Round: {context.get('hr_round_score')}
Technical Round: {context.get('tech_round_score')}
Case Study Round: {context.get('case_study_round_score')}
Final Round: {context.get('final_round_score')}
Management / Client Round: {context.get('management_client_round_score')}

━━━━━━━━━━━━━━━━━━
*Offer & Other Details*
━━━━━━━━━━━━━━━━━━
Current / Last Drawn CTC: {context.get('current_ctc')}
Expected CTC: {context.get('expected_ctc')}
CTC to be Offered: {context.get('offered_ctc')}
Notice Period: {context.get('notice_period')}
Office Location: {context.get('office_location')}
Source: {context.get('source')}
MRF: {context.get('mrf')}
New / Replacement: {context.get('hiring_type')}
Remarks: {context.get('remarks') or 'N/A'}

━━━━━━━━━━━━━━━━━━

Please review the details and share your feedback.

View Candidate Profile:
{context.get('FRONTEND_URL')}/onboarding

Regards,
Team – HR
Knowcraft Analytics Private Limited
"""

        # --- Trigger workflow ---
        try:
            candidate.joining_date = data.get("joining_date")
            candidate.save()
            ok,reason = automation_engine(candidate, candidate.status, "approval_pending")
            if ok:
                json_safe_context = {
                    key: make_json_safe(value)
                    for key, value in context.items()
                }

                approval_note = ApprovalNote.objects.create(
                    candidate=candidate,
                    manager=approver,
                    created_by=request.user,
                    payload=json_safe_context
                )
                from .utils.resume_attachment import get_resume_attachment
                resume_attachment = get_resume_attachment(candidate)
                # --- Send email (Suppressed for private jobs) ---
                if approval_note and not candidate.job.is_private:
                    send_email(
                        subject="Approval Required – Candidate Hiring",
                        text="Approval required. Please view this email in HTML format.",
                        to=approver.email,
                        template=html_rendered,
                        attachments=[resume_attachment] if resume_attachment else None,
                        event="approval_note_sent",
                        email_type="approval",
                        candidate=candidate
                    )
                    if approver.phone:
                        send_text(to=approver.phone,text=whatsapp_text)
                        send_document(to=approver.phone,text="Candidate Resume",file_url=candidate.resume.url,filename=f'{candidate.candidate_name}_Resume.pdf')
                elif approval_note and candidate.job.is_private:
                    print(f"Skipping Approval Note notification for private job: {candidate.job.id}")

            else:
                print(reason)

        except Exception as e:
            return Response(f"Unable to send the Approval Note:{e}",status=400)

        return Response(
            {"status": "Approval note sent successfully"},
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        user = request.user
        if user.role not in ['hr', 'admin', 'hr_manager']:
            return Response(
                {"detail": "Only HR or admin can update approval notes."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            approval_note_id = request.data.get("approval_note_id")
            if not approval_note_id:
                return Response(
                    {"detail": "approval_note_id is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            approval_note = ApprovalNote.objects.get(id=approval_note_id)
        except ApprovalNote.DoesNotExist:
            return Response({"detail": "Approval note not found."}, status=status.HTTP_404_NOT_FOUND)

        if approval_note.created_by != user and user.role != 'admin':
            return Response(
                {"detail": "You can only update notes you created."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Allowed editable fields
        editable_fields = {
            'designation': 'designation',
            'current_ctc': 'current_ctc',
            'expected_ctc': 'expected_ctc',
            'offered_ctc': 'offered_ctc',
            'joining_date': 'joining_date',
            'notice_period': 'notice_period',
            'department': 'department',
            "remarks": "remarks",
            "hiring_type": "hiring_type",
            "office_location": "office_location",
        }

        data = request.data
        updated_fields = []
        current_payload = approval_note.payload or {}

        for key, payload_key in editable_fields.items():
            if key in data:
                if key == 'joining_date':
                    # Parse date safely
                    date_str = data[key]
                    try:
                        parsed_date = parser.parse(date_str).date()
                        current_payload[payload_key] = parsed_date.isoformat()
                        # Sync to JobApplication
                        approval_note.candidate.joining_date = parsed_date
                        approval_note.candidate.save()
                    except ValueError:
                        return Response(
                            {"detail": f"Invalid date format for {key}. Use YYYY-MM-DD."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    current_payload[payload_key] = data[key]
                updated_fields.append(payload_key)

        if not updated_fields:
            return Response(
                {"detail": "No valid fields provided for update."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update payload
        approval_note.payload = current_payload
        approval_note.updated_at = timezone.now()
        # Save only the payload and updated_at to prevent overwriting status changes
        # that were applied in the JobApplication.save() method.
        approval_note.save(update_fields=['payload', 'updated_at'])
        
        # Refresh from db so that the in-memory object reflects the new status 
        # (e.g., 'joining_pending' if it was reverted)
        approval_note.refresh_from_db()

        return Response(
            {
                "detail": "Approval note updated successfully",
                "updated_fields": updated_fields,
                "payload": approval_note.payload
            },
            status=status.HTTP_200_OK
        )

def aggregate_interview_feedback(job_application):
    feedbacks = job_application.interview_feedbacks.all()

    result = {
        # Interviewers
        "hr_round_interviewer": None,
        "tech_round_interviewer": None,
        "case_study_round_interviewer": None,
        "final_round_interviewer": None,
        "management_client_round_interviewer": None,

        # ---- Scores ----
        "hr_round_score": None,
        "tech_round_score": None,
        "case_study_round_score": None,
        "final_round_score": None,
        "management_client_round_score": None,

        # ---- Common fields ----
        "qualification": None,
        "last_organization": None,
        "notice_period": None,
        "current_ctc": None,
        "expected_ctc": None,
        "remarks": None,
    }

    for fb in feedbacks:
        # ---- Round-wise mapping ----
        if fb.interview_round == "hr_round":
            result["hr_round_interviewer"] = fb.interviewer_name
            result["hr_round_score"] = fb.get_round_avg()

        elif fb.interview_round == "technical_round":
            result["tech_round_interviewer"] = fb.interviewer_name
            result["tech_round_score"] = fb.get_round_avg()

        elif fb.interview_round == "case_study_round":
            result["case_study_round_interviewer"] = fb.interviewer_name
            result["case_study_round_score"] = fb.get_round_avg()

        elif fb.interview_round == "final_round":
            result["final_round_interviewer"] = fb.interviewer_name
            result["final_round_score"] = fb.get_round_avg()

        elif fb.interview_round == "management_client_round":
            result["management_client_round_interviewer"] = fb.interviewer_name
            result["management_client_round_score"] = fb.get_round_avg()

        # ---- Common fields (first non-null wins) ----
        result["qualification"] = result["qualification"] or fb.qualification
        result["last_organization"] = result["last_organization"] or fb.current_organization
        result["notice_period"] = result["notice_period"] or fb.notice_period
        result["current_ctc"] = result["current_ctc"] or fb.current_ctc
        result["expected_ctc"] = result["expected_ctc"] or fb.expected_ctc
        result["remarks"] = result["remarks"] or fb.comments

    return result

class CandidateInterviewSummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, candidate_id):
        candidate = get_object_or_404(JobApplication, id=candidate_id)
        mrf = candidate.job.mrf
        manager = mrf.requested_by
        feedback_data = aggregate_interview_feedback(candidate)
        hiring_type = "Replacement" if mrf.resigned_crafter_name else "New Position"
        response = {
            "candidate_id": str(candidate.id),
            "candidate_name": candidate.candidate_name,
            "experience": candidate.experience_years,
            "designation": candidate.job.mrf.designation.name,
            "department": candidate.job.mrf.department.name,
            "manager_name": manager.name,
            "manager_email": manager.email,
            "hiring_type": hiring_type,
            "offered_ctc": "",
            "office_location": candidate.job.mrf.location,
            "source": candidate.source,
            "mrf": mrf.mrf_name,
            **feedback_data
        }

        return Response(response, status=status.HTTP_200_OK)

class SalaryAnnexureViewSet(ModelViewSet):
    queryset = SalaryAnnexure.objects.select_related("job_application")
    serializer_class = SalaryAnnexureSerializer

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        # Apply privacy filter
        # Admins and HR managers can see ALL records (including private ones)
        if user.role not in ['admin', 'hr_manager']:
            qs = qs.filter(
                Q(job_application__job__is_private=False) |
                Q(job_application__job__is_private=True, job_application__job__posted_by=user) |
                Q(job_application__job__is_private=True, job_application__job__selected_viewers=user) |
                Q(job_application__job__is_private=True, job_application__job__assigned_to_consultancy=user) |
                Q(job_application__job__is_private=True, job_application__job__assigned_to_internal_hr=user) |
                Q(job_application__job__is_private=True, job_application__job__assigned_internal_hrs=user) |
                Q(job_application__job__is_private=True, job_application__job__assigned_consultancies=user)
            )

        candidate_id = self.request.query_params.get("candidate_id")

        if candidate_id:
            qs = qs.filter(job_application_id=candidate_id)

        return qs


    def perform_create(self, serializer):
        annexure = serializer.save(prepared_by=self.request.user)
        log_salary_annexure_history(
            annexure,
            action="created",
            user=self.request.user
        )

        #Send directly after create
        annexure.status = "sent"
        annexure.rejection_reason = ""
        annexure.save(update_fields=["status", "rejection_reason"])

        app = annexure.job_application
        ok,reason = automation_engine(app, app.status, "salary_annexure_review")
        if ok:
            log_salary_annexure_history(
                annexure,
                action="sent",
                user=self.request.user
            )
            send_salary_annexure_email(annexure, self.request.user)

            return Response({"message": "Salary annexure sent for approval"})
        else:
            return Response({"error": reason})
    
    def perform_update(self, serializer):
        annexure = serializer.save()

        log_salary_annexure_history(
            annexure,
            action="updated",
            user=self.request.user,
            remarks="Annexure updated"
        )

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        annexure = self.get_object()

        if annexure.status in ["rejected", "approved", "sent"]:
            return Response(
                {"error": f"Cannot sent annexure in '{annexure.status}' state"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        annexure.status = "sent"
        annexure.rejection_reason = ""
        annexure.save(update_fields=["status", "rejection_reason"])

        app = annexure.job_application
        ok,reason = automation_engine(app, app.status, "salary_annexure_review")
        if ok:
            log_salary_annexure_history(
                annexure,
                action="sent",
                user=request.user
            )
            send_salary_annexure_email(annexure, self.request.user)

            return Response({"message": "Salary annexure sent for approval"})
        else:
            return Response({"error": reason})

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        annexure = self.get_object()
        
        if annexure.status == "draft":
            return Response(
                {"error": f"Can't approve annexure.Annexure is not sent for approval."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        annexure.status = "approved"
        annexure.reviewed_by = request.user
        annexure.save(update_fields=["status", "reviewed_by"])

        app = annexure.job_application
        ok,reason = automation_engine(app, app.status, "approved_annexure")
        if ok:
            log_salary_annexure_history(
                annexure,
                action="approved",
                user=request.user
            )

            return Response({"message": "Salary annexure approved"})
        else:
            return Response({"error": reason})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        reason = request.data.get("reason")
        if not reason:
            return Response(
                {"error": "Rejection reason is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        annexure = self.get_object()

        if annexure.status == "approved":
            return Response(
                {"error": "Approved annexure cannot be rejected"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # allow revision only after rejection or draft
        if annexure.status == "rejected":
            return Response(
                {"error": f"Annexure is already rejected"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if annexure.status == "draft":
            return Response(
                {"error": f"Can't reject annexure.Annexure is not sent for approval."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        annexure.status = "rejected"
        annexure.reviewed_by = request.user
        annexure.rejection_reason = reason
        annexure.save(update_fields=[
            "status",
            "reviewed_by",
            "rejection_reason",
            "revision_count"
        ])

        app = annexure.job_application
        ok,reason = automation_engine(app, app.status, "rejected_annexure")
        if ok:
            log_salary_annexure_history(
                annexure,
                action="rejected",
                user=request.user,
                remarks=annexure.rejection_reason
            )

            return Response({"message": "Salary annexure rejected"})
        else:
            return Response({"error": reason})

    @action(detail=True, methods=["post"])
    def revise(self, request, pk=None):
        annexure = self.get_object()

        # ❌ Cannot revise an approved annexure
        if annexure.status == "approved":
            return Response(
                {"error": "Approved annexure cannot be revised"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Optional: only allow revision after rejection
        if annexure.status not in ["rejected", "draft"]:
            return Response(
                {"error": f"Cannot revise annexure in '{annexure.status}' state"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update editable fields
        editable_fields = [
            "designation",
            "effective_from",
            "gross_monthly",
            "ctc_annual",
            "net_monthly",
            "notes",
        ]

        updated = False
        for field in editable_fields:
            if field in request.data:
                setattr(annexure, field, request.data[field])
                updated = True

        if not updated:
            return Response(
                {"error": "No valid fields provided for revision"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reset review metadata
        annexure.status = "draft"
        annexure.rejection_reason = None
        annexure.reviewed_by = None
        annexure.revision_count += 1
        annexure.prepared_by = request.user
        
        components_data = request.data.get("components")

        if components_data is not None:
            annexure.components.all().delete()  # simple & safe

            for comp in components_data:
                comp.pop("id", None)
                SalaryComponent.objects.create(
                    annexure=annexure,
                    **comp
                )

        annexure.save()

        # 🔁 Move workflow back to salary_annexure_prep
        app = annexure.job_application
        ok,reason = automation_engine(app, app.status, "salary_annexure_prep")
        if ok:
            log_salary_annexure_history(
                annexure,
                action="revised",
                user=request.user,
                remarks=annexure.notes
            )

            #Send directly after revise
            annexure.status = "sent"
            annexure.rejection_reason = ""
            annexure.save(update_fields=["status", "rejection_reason"])

            app = annexure.job_application
            ok,reason = automation_engine(app, app.status, "salary_annexure_review")
            if ok:
                log_salary_annexure_history(
                    annexure,
                    action="sent",
                    user=self.request.user
                )
                send_salary_annexure_email(annexure, self.request.user)
            return Response(
                {
                    "message": "Salary annexure revised successfully",
                    "revision_count": annexure.revision_count
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response({"error": reason})
    
class SalaryAnnexureHistoryViewSet(ReadOnlyModelViewSet):
    serializer_class = SalaryAnnexureHistorySerializer

    def get_queryset(self):
        """
        Filter by annexure or job application
        """
        user = self.request.user
        qs = SalaryAnnexureHistory.objects.select_related(
            "annexure",
            "performed_by"
        )

        # Apply privacy filter
        # Admins and HR managers can see ALL records (including private ones)
        if user.role not in ['admin', 'hr_manager']:
            qs = qs.filter(
                Q(annexure__job_application__job__is_private=False) |
                Q(annexure__job_application__job__is_private=True, annexure__job_application__job__posted_by=user) |
                Q(annexure__job_application__job__is_private=True, annexure__job_application__job__selected_viewers=user) |
                Q(annexure__job_application__job__is_private=True, annexure__job_application__job__assigned_to_consultancy=user) |
                Q(annexure__job_application__job__is_private=True, annexure__job_application__job__assigned_to_internal_hr=user) |
                Q(annexure__job_application__job__is_private=True, annexure__job_application__job__assigned_internal_hrs=user) |
                Q(annexure__job_application__job__is_private=True, annexure__job_application__job__assigned_consultancies=user)
            )

        annexure_id = self.request.query_params.get("annexure_id")
        job_application_id = self.request.query_params.get("job_application_id")

        if annexure_id:
            qs = qs.filter(annexure_id=annexure_id)

        if job_application_id:
            qs = qs.filter(
                annexure__job_application_id=job_application_id
            )

        return qs.order_by("created_at")
    
class SendForOfferLetterEmailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        job_application = get_object_or_404(JobApplication, id=id)

        recipient_email = request.data.get("email")
        recipient_phone = request.data.get("phone")
        joining_date = request.data.get("joining_date") or job_application.joining_date
        offer_letter_upload_link = f"{settings.FRONTEND_URL}/review-documents/{id}"

        if not recipient_email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        subject = "Document View Required - Offer Letter Creation"

        message = f"""
Hello,

You have been requested to view the salary annexure for the candidate:
{job_application.candidate_name}

Joining Date: {joining_date.strftime("%d-%m-%Y") if joining_date else ""}

After reviewing, kindly generate and upload the offer letter.

Thank you.
"""
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
                                    <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;line-height:1.5;">
                                        <p style="margin:0 0 16px 0;">Dear Team,</p>
                                        <p style="margin:0 0 16px 0;">A request has been raised to review the salary annexure for the following candidate:</p>
                                        
                                        <p style="margin:0 0 8px 0;font-weight:600;">Candidate Name: {job_application.candidate_name}</p>
                                        <p style="margin:0 0 24px 0;font-weight:600;">Proposed Joining Date: {joining_date.strftime("%d-%m-%Y") if joining_date else "TBD"}</p>
                                        
                                        <p style="margin:0 0 24px 0;">Kindly review the salary annexure details in the system. Once reviewed, please generate and upload the formal offer letter at your earliest convenience to proceed with the next steps.</p>
                                        
                                        <p style="margin:25px 0 30px 0;text-align:center;">
                                            <a href="{offer_letter_upload_link}" 
                                            style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">View Annexure & Generate Offer Letter</a>
                                        </p>
                                        
                                        <p style="margin:0 0 16px 0;">If you require any additional information or clarification, please do not hesitate to reach out.</p>
                                        <br>
                                        <p style="margin:20px 0 6px 0;color:#555555;">Thank you for your prompt attention to this matter.</p>
                                        <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                        <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>"""
        from .utils.annexure_attachment import get_annexure_attachment
        annexure_attachment = get_annexure_attachment(job_application.documents)
        
        is_private = job_application.job.is_private

        if not is_private:
            send_email(
                subject=subject,
                text=message,
                to=recipient_email,
                template=template,
                attachments=[annexure_attachment] if annexure_attachment else None,
                event="salary_annexure_sent",
                email_type="candidate",
                candidate=job_application
            )
        else:
            print(f"Skipping Offer Letter notification for private job: {job_application.job.id}")

        if recipient_phone and not is_private:
            send_text(to=recipient_phone,text=message)
            if annexure_attachment:
                send_document(to=recipient_phone,text="Salary Annexure",filename=f"{job_application.candidate_name}_annexure.pdf",file_url=job_application.docs.salary_annexure.url)
        automation_engine(job_application,job_application.status,"offer_pending")
        return Response(
            {"message": "Review email sent successfully!"},
            status=status.HTTP_200_OK
        )

from .models import OfferDocument
from .utils.zoho_sign import recall_zoho_offer

class RevertOfferAPIView(APIView):
    """
    Recalls an active offer from Zoho Sign, deletes the OfferDocument,
    clears the offer letter file, and reverts the application status
    to 'offer_pending' so HR can update and resend.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        job_application = get_object_or_404(JobApplication, id=id)

        # 1. Recall from Zoho Sign if exists
        offer = OfferDocument.objects.filter(application=job_application).first()
        if offer:
            if job_application.status in ['offer_pending','offer_accepted','offer_rejected','offer_sent','joining_pending']:
                recall_zoho_offer(offer)
            # 2. Delete OfferDocument so the system knows no offer is active
            offer.delete()

        # 3. Clear the created offer letter file from documents
        if hasattr(job_application, 'documents'):
            docs = job_application.documents
            if docs.created_offer_letter:
                # Optionally delete the physical file
                # docs.created_offer_letter.delete(save=False)
                docs.created_offer_letter = None
                docs.save()

        # 4. Revert status back to offer_pending
        job_application.status = "offer_pending"
        job_application.save(update_fields=["status"])
        
        if hasattr(job_application, 'approval_note'):
            note = job_application.approval_note
            note.status = "offer_pending"
            note.save(update_fields=["status"])

        return Response(
            {"message": "Offer successfully reverted to pending stage."},
            status=status.HTTP_200_OK
        )


class SendForSalaryAnnexureEmailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        job_application = get_object_or_404(JobApplication, id=id)

        recipient_email = request.data.get("email")
        recipient_phone = request.data.get("phone")
        offered_ctc = request.data.get("offered_ctc")
        joining_date = request.data.get("joining_date") or job_application.joining_date

        if not recipient_email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔗 Build review link
        review_link = f"{settings.FRONTEND_URL}/upload-salary-annexure/{id}"

        subject = "Document View Required - Salary Annexure Upload"

        message = f"""
Hello,

You have been requested to view the documents for the candidate:
{job_application.candidate_name}

Please review the documents and upload the Salary Annexure using the link below:
{review_link}

Offered CTC: {offered_ctc}

Joining Date: {joining_date.strftime("%d-%m-%Y") if joining_date else ""}

After reviewing, kindly generate and upload the salary annexure.

Thank you.
"""
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
                                    <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;line-height:1.5;">
                                        <p style="margin:0 0 16px 0;">Dear Team,</p>
                                        <p style="margin:0 0 16px 0;">The following candidate has submitted their joining documents for review:</p>
                                        
                                        <p style="margin:0 0 8px 0;font-weight:600;">Candidate Name: {job_application.candidate_name}</p>
                                        <p style="margin:0 0 8px 0;font-weight:600;">Offered CTC: {offered_ctc}</p>
                                        <p style="margin:0 0 24px 0;font-weight:600;">Proposed Joining Date: {joining_date.strftime("%d-%m-%Y") if joining_date else "TBD"}</p>
                                        
                                        <p style="margin:0 0 16px 0;">Please review the uploaded documents thoroughly and upload the finalized Salary Annexure using the link below.</p>
                                        
                                        <p style="margin:25px 0 30px 0;text-align:center;">
                                            <a href="{review_link}" 
                                            style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Review Documents & Upload Salary Annexure</a>
                                        </p>
                                        
                                        <p style="margin:0 0 16px 0;">Ensure all details align with the offer terms before proceeding. If any discrepancies or clarifications are needed, please contact the HR team promptly.</p>
                                        <br>
                                        <p style="margin:20px 0 6px 0;color:#555555;">Thank you for your support in streamlining the onboarding process.</p>
                                        <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                        <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        from .utils.resume_attachment import get_resume_attachment
        resume_attachment = get_resume_attachment(job_application)

        is_private = job_application.job.is_private

        if not is_private:
            send_email(
                subject=subject,
                text=message,
                to=recipient_email,
                template=template,
                attachments=[resume_attachment] if resume_attachment else None,
                event="offer_letter_sent",
                email_type="candidate",
                candidate=job_application
            )
        else:
            print(f"Skipping Salary Annexure Prep notification for private job: {job_application.job.id}")

        if recipient_phone and not is_private:
            send_text(to=recipient_phone,text=message)
            send_document(to=recipient_phone,text="Candidate Resume",file_url=job_application.resume.url,filename=f'{job_application.candidate_name}_Resume.pdf')
        automation_engine(job_application, job_application.status, "salary_annexure_prep")
        return Response(
            {"message": "Salary Annexure review email sent successfully!"},
            status=status.HTTP_200_OK
        )

from .models import DocuSignOffer
# from .serializers import DocuSignOfferSerializer
# from onboarding.utils.docusign import send_offer_via_docusign
# import hmac
# import hashlib

# class BulkSendOffersAPI(APIView):
#     permission_classes = [permissions.IsAuthenticated]  # Adjust as needed
    
#     def post(self, request):
#         application_ids = request.data.get('application_ids', [])
#         if not application_ids:
#             return Response({"error": "No application IDs provided"}, status=400)
        
#         results = {'success': [], 'failed': []}
#         for app_id in application_ids:
#             try:
#                 application = JobApplication.objects.get(id=app_id)
#                 if application.docusign_offer and application.docusign_offer.status == 'sent':
#                     results['failed'].append({'id': app_id, 'reason': 'Already sent'})
#                     continue
                
#                 # Assume offer exists; generate if not (extend OfferDocument logic if needed)
#                 if not hasattr(application, 'offerdocument') or not application.offerdocument:
#                     # Placeholder: create offer doc if missing
#                     pass  # Implement offer generation
                
#                 ok, result = send_offer_via_docusign(application)
#                 if ok:
#                     results['success'].append({'id': app_id, 'envelope_id': result})
#                     # Trigger automation if needed
#                     automation_engine(application, application.status, 'offer_sent')
#                 else:
#                     results['failed'].append({'id': app_id, 'reason': result})
#             except JobApplication.DoesNotExist:
#                 results['failed'].append({'id': app_id, 'reason': 'Application not found'})
        
#         return Response(results)

# class DocuSignWebhookAPI(APIView):
#     permission_classes = [permissions.AllowAny]  # Webhook no auth, but verify below
    
#     def post(self, request):
#         data = request.data
#         if not isinstance(data, list):
#             return Response(status=400)
        
#         for event in data:
#             envelope_id = event.get('envelopeId')
#             status = event.get('status')
            
#             try:
#                 docusign_offer = DocuSignOffer.objects.get(envelope_id=envelope_id)
#                 old_status = docusign_offer.status
#                 docusign_offer.status = status.lower()
                
#                 if status.lower() == 'completed':
#                     docusign_offer.signed_date = event.get('completedDateTime')
#                     # Get signing URL or details if needed
#                     docusign_offer.signed_url = event.get('signedUrl', '')  # Adjust from event
                
#                 docusign_offer.save()
                
#                 application = docusign_offer.job_application
#                 # Trigger status update based on DocuSign status
#                 if status.lower() == 'completed':
#                     automation_engine(application, application.status, 'offer_signed')
#                 elif status.lower() in ['declined', 'voided']:
#                     automation_engine(application, application.status, 'offer_declined')
                
#                 logger.info(f"Webhook updated {envelope_id}: {old_status} -> {status}")
                
#             except DocuSignOffer.DoesNotExist:
#                 logger.warning(f"Webhook for unknown envelope: {envelope_id}")
        
#         return Response({"status": "received"}, status=200)


from .utils.docusign import DocuSignService
from django.http import JsonResponse
def send_offer_letter_view(request, application_id):
    try:
        application = JobApplication.objects.get(id=application_id)
        if application.job.is_private:
            return JsonResponse({"error": "Cannot send DocuSign offer for private job. Communication is suppressed."}, status=400)


        if not application.candidate_email:
            return JsonResponse({"error": "Candidate email missing"}, status=400)

        service = DocuSignService()
        envelope_id = service.send_offer(application)

        # Create or update DocuSignOffer
        offer, created = DocuSignOffer.objects.update_or_create(
            job_application=application,
            defaults={
                "envelope_id": envelope_id,
                "status": "sent",
                "signer_email": application.candidate_email,
            }
        )

        # Update main status
        application.status = "offer_sent"
        application.save()

        return JsonResponse({
            "message": "Offer sent successfully",
            "envelope_id": envelope_id,
            "created": created
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def bulk_send_offers(request):
    applications = JobApplication.objects.filter(
        status="approved",
        candidate_email__isnull=False,
        job__is_private=False
    )

    service = DocuSignService()
    success_count = 0

    for app in applications:
        try:
            envelope_id = service.send_offer(app)

            DocuSignOffer.objects.update_or_create(
                job_application=app,
                defaults={
                    "envelope_id": envelope_id,
                    "status": "sent",
                    "signer_email": app.candidate_email,
                }
            )

            app.status = "offer_sent"
            app.save()

            success_count += 1

        except Exception as e:
            print(f"Error sending to {app.id}: {str(e)}")

    return JsonResponse({
        "message": "Bulk offers sent",
        "count": success_count
    })

import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import xmltodict

@csrf_exempt
def docusign_webhook(request):
    try:
        print("🔥 WEBHOOK HIT")

        content_type = request.content_type  # Fixed typo: content_ytpe -> content_type
        print("Content-Type:", content_type)

        # 🧠 Handle JSON
        if "application/json" in content_type:
            data = json.loads(request.body)

        # 🧠 Handle XML (DocuSign default)
        else:
            data = xmltodict.parse(request.body)

            # Extract actual data
            data = data.get("DocuSignEnvelopeInformation", {})
        
        print("Parsed Data:", data)

        envelope_id = data.get("envelopeId")
        status = data.get("status")

        print(f"Envelope: {envelope_id}, Status: {status}")

        offer = DocuSignOffer.objects.filter(envelope_id=envelope_id).first()

        if not offer:
            print("Offer not found")
            return HttpResponse(status=200)

        # ✅ Status mapping
        if status == "completed":
            offer.status = "signed"
            offer.signed_date = timezone.now()
            offer.job_application.offer_accepted_date = offer.signed_date.date()
            offer.job_application.save()
            automation_engine(offer.job_application, offer.job_application.status, "offer_accepted")

        elif status == "declined":
            offer.status = "declined"
            automation_engine(offer.job_application, offer.job_application.status, "offer_rejected")

        elif status == "voided":
            offer.status = "voided"

        offer.save()

        return HttpResponse(status=200)

    except Exception as e:
        print("❌ Webhook Error:", str(e))
        return HttpResponse(status=400)

import zipfile
import io
import os
import requests
from django.http import StreamingHttpResponse,Http404
# from azure.storage.blob import BlobServiceClient

class DownloadJobApplicationDocumentsView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, id):
        try:
            candidate = JobApplication.objects.filter(id=id).first()
            if not candidate:
                raise Http404("No candidate found for the provided ID") 
            
            docs = JobApplicationDocument.objects.filter(job_application=candidate).first()
            if not docs:
                raise Http404("No documents found for the provided IDs")

            download_files = []
            for field in docs._meta.get_fields():
                if isinstance(field, FileField):
                    file_name = field.name

                    if hasattr(docs, file_name):
                        docu = getattr(docs, file_name)
                        if not docu:
                            continue
                        download_files.append(docu)

            if not download_files:
                raise Http404("No documents found for the provided IDs")

            in_memory_zip = io.BytesIO()
            if settings.USE_AZURE_MEDIA:
                # Azure Blob connection
                # connection_string = f"DefaultEndpointsProtocol=https;AccountName={settings.AZURE_ACCOUNT_NAME};AccountKey={settings.AZURE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
                # print(connection_string,'======================CONNECTION STRING======================')
                # blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                
                with zipfile.ZipFile(in_memory_zip, mode='w') as zipf:
                    for download_file in download_files:
                        file_path = download_file.url
                        if file_path:
                            file_path = file_path.split("?")[0]
                        original_filename = os.path.basename(file_path)
                        prefix, extension = os.path.splitext(original_filename)
                        modified_filename = f"{original_filename}{extension}".replace('_',' ').title()

                        # Get blob client
                        # blob_client = blob_service_client.get_blob_client(
                        #     container=settings.AZURE_CONTAINER,
                        #     blob=file_path
                        # )

                        # # Download blob content
                        # blob_data = blob_client.download_blob().readall()

                        # # Add file to ZIP
                        # zipf.writestr(
                        #     f'{candidate.candidate_name}_{modified_filename}',
                        #     blob_data)
                        response = requests.get(file_path)
                        if response.status_code == 200:
                            zipf.writestr(
                                f'{candidate.candidate_name}_{modified_filename}',
                                response.content
                            )
                        else:
                            print(f"Failed to download: {file_path}")
            else:
                with zipfile.ZipFile(in_memory_zip, mode='w') as zipf:
                    for download_file in download_files: 
                        file_path = download_file.url
                        original_filename = os.path.basename(file_path)
                        prefix, extension = os.path.splitext(original_filename)
                        modified_filename = f"{original_filename}{extension}".replace('_',' ').title()
                        zipf.write(file_path, arcname=f'{candidate.candidate_name}_{modified_filename}')

            in_memory_zip.seek(0)
            response = StreamingHttpResponse(in_memory_zip, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{candidate.candidate_name} Documents.zip"'
            return response

        except JobApplicationDocument.DoesNotExist:
            raise Http404("One or more documents do not exist")
        except Exception as e:
            return HttpResponse(f'Error creating zip file: {str(e)}', status=404)

class DownloadApprovalNoteAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        note = get_object_or_404(ApprovalNote, id=id)
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            from io import BytesIO
            import json

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()

            # Header with Logo
            title = f"Approval Note: {note.candidate.candidate_name if note.candidate else 'Unknown'}"
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.platypus import Image
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                alignment=0, # Left align
                textColor=colors.HexColor('#0B3D91'),
                fontSize=22,
                spaceAfter=0
            )
            
            logo_url = "https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png"
            try:
                import urllib.request
                import io
                req = urllib.request.Request(logo_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    img_data = io.BytesIO(response.read())
                logo = Image(img_data, width=150, height=45)
                header_data = [[Paragraph(title, title_style), logo]]
                col_widths = [350, 150]
            except Exception as e:
                print(f"Error loading logo: {e}")
                header_data = [[Paragraph(title, title_style), ""]]
                col_widths = [400, 100]

            header_table = Table(header_data, colWidths=col_widths)
            header_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 15),
                ('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor('#0B3D91')),
            ]))
            
            elements.append(header_table)
            elements.append(Spacer(1, 15))

            # Custom Styles
            normal_style = styles['Normal']
            normal_style.fontSize = 10
            normal_style.textColor = colors.HexColor('#333333')
            normal_style.leading = 14
            
            label_style = ParagraphStyle(
                'LabelStyle',
                parent=normal_style,
                fontName='Helvetica-Bold',
                textColor=colors.HexColor('#0B3D91'),
            )

            heading_style = ParagraphStyle(
                'HeadingStyle',
                parent=styles['Heading2'],
                textColor=colors.HexColor('#0B3D91'),
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20,
                borderPadding=0,
            )

            # Basic Info
            elements.append(Paragraph("Basic Information", heading_style))
            basic_data = [
                [Paragraph("Candidate Name", label_style), Paragraph(note.candidate.candidate_name if note.candidate else "N/A", normal_style)],
                [Paragraph("Current Status", label_style), Paragraph(dict(ApprovalNote.STATUS_CHOICES).get(note.status,note.status), normal_style)],
                [Paragraph("Approver", label_style), Paragraph(note.manager.name if note.manager else "N/A", normal_style)],
                [Paragraph("Requested By", label_style), Paragraph(note.created_by.name if note.created_by else "N/A", normal_style)],
                [Paragraph("Requested At", label_style), Paragraph(str(note.created_at.date()) if note.created_at else "N/A", normal_style)]
            ]
            
            t = Table(basic_data, colWidths=[150, 350])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F4F6FB')),
                ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#333333')),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('PADDING', (0,0), (-1,-1), 10),
                ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#E6EBF5')),
                ('LINEABOVE', (0,0), (-1,0), 1, colors.HexColor('#E6EBF5')),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 10))

            # Payload Data
            elements.append(Paragraph("Detailed Information", heading_style))

            if isinstance(note.payload, dict):
                payload_data = []
                for k, v in note.payload.items():
                    k_str = str(k).replace('_', ' ').title()
                    if isinstance(v, dict) or isinstance(v, list):
                        v_str = json.dumps(v, indent=2)
                    else:
                        v_str = str(v)
                    payload_data.append([
                        Paragraph(f"• {k_str}", label_style), 
                        Paragraph(v_str, normal_style)
                    ])
                
                if payload_data:
                    pt = Table(payload_data, colWidths=[200, 300])
                    pt.setStyle(TableStyle([
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('PADDING', (0,0), (-1,-1), 10),
                        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#E6EBF5')),
                    ]))
                    elements.append(pt)
            else:
                elements.append(Paragraph(str(note.payload), normal_style))

            doc.build(elements)
            buffer.seek(0)

            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="approval_note_{note.candidate.candidate_name}.pdf"'
            return response
            
        except Exception as e:
            # Fallback to JSON if reportlab fails
            import json
            data = {
                "id": str(note.id),
                "candidate_name": note.candidate.candidate_name if note.candidate else None,
                "manager": note.manager.name if note.manager else None,
                "created_by": note.created_by.name if note.created_by else None,
                "status": note.status,
                "payload": note.payload
            }
            response = HttpResponse(json.dumps(data, indent=4), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="approval_note_{note.candidate.candidate_name}.json"'
            return response

class EmailLogViewSet(ReadOnlyModelViewSet):
    """
    API View to list all emails sent out from the system.
    Supports filtering by email, event, status, type, and candidate.
    """
    queryset = EmailLog.objects.all().order_by('-sent_at')
    serializer_class = EmailLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Only HR/Admin can see email audit logs
        if user.role !='admin':
            return EmailLog.objects.none()

        qs = super().get_queryset()

        recipient = self.request.query_params.get("recipient_email")
        if recipient:
            qs = qs.filter(recipient_email__icontains=recipient)

        event = self.request.query_params.get("event")
        if event:
            qs = qs.filter(event=event)

        status_val = self.request.query_params.get("status")
        if status_val:
            qs = qs.filter(status=status_val)

        email_type = self.request.query_params.get("email_type")
        if email_type:
            qs = qs.filter(email_type=email_type)
            
        candidate_id = self.request.query_params.get("candidate_id")
        if candidate_id:
            qs = qs.filter(candidate_id=candidate_id)

        return qs

# --- Onboarding Post-Joining APIs ---

class InitiateOnboardingAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        application = get_object_or_404(JobApplication, id=id)
        
        # Extract full form data as per the ME onboarding form
        form_data = {
            "assets": request.data.get("assets"),
            "site": request.data.get("site"),
            "subject": request.data.get("subject"),
            "first_name": request.data.get("first_name"),
            "last_name": request.data.get("last_name"),
            "personal_email_id": request.data.get("personal_email_id"),
            "contact_number": request.data.get("contact_number"),
            "joining_date": request.data.get("joining_date"),
            "designation": request.data.get("designation"),
            "department": request.data.get("department"),
            "employee_category": request.data.get("employee_category"),
            "center_office_location": request.data.get("center_office_location"),
            "mode_for_collecting_assets": request.data.get("mode_for_collecting_assets"),
            "team_manager": request.data.get("team_manager"),
            "work_from": request.data.get("work_from"),
            "crafter_id": request.data.get("crafter_id"),
            "emails_to_notify": request.data.get("emails_to_notify"),
            "current_address": request.data.get("current_address"),
            "description": request.data.get("description"),
            "custom_notes": request.data.get("custom_notes", ""),
            "requester_email_id": request.data.get("requester_email_id"),
            "requester_name": request.data.get("requester_name"),
            "requester_id": request.data.get("requester_id"),
            "attachment_files": request.FILES.getlist("attachments"),
        }
        
        try:
            from onboarding.utils.zoho_manageengine import ManageEngineClient
            from onboarding.models import OnboardingForm
            me_client = ManageEngineClient()
            ticket_id = me_client.create_onboarding_ticket(application, form_data=form_data)
            
            if ticket_id:
                application.it_ticket_ref = ticket_id
                application.save(update_fields=['it_ticket_ref'])
                
                # Persist the onboarding form data
                OnboardingForm.objects.update_or_create(
                    job_application=application,
                    defaults={
                        'submitted_by': request.user if request.user.is_authenticated else None,
                        'ticket_ref': ticket_id,
                        **{k: v for k, v in form_data.items() if k != 'custom_notes'},
                        'custom_notes': form_data.get('custom_notes', ''),
                    }
                )
                
                # Notify IT Team
                from onboarding.utils.notifications import notify_internal
                notify_internal(application, 'it_team_ticket_created')
                
                return Response({
                    "message": "Onboarding initiated and IT ticket created successfully.",
                    "ticket_id": ticket_id
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed to create IT ticket."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error initiating onboarding for {application.id}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResolveEscalationAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def patch(self, request, id):
        application = get_object_or_404(JobApplication, id=id)
        application.is_escalated = False
        application.save(update_fields=['is_escalated'])
        return Response({"message": "Escalation resolved successfully"}, status=status.HTTP_200_OK)

class SearchTeamsUsersAPI(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        query = request.query_params.get("query", "")
        try:
            from slots.graph import get_graph_token
            import requests
            token = get_graph_token()
            url = "https://graph.microsoft.com/v1.0/users"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "$select": "id,displayName,mail,userPrincipalName",
                "$top": "50"
            }
            if query:
                params["$filter"] = f"startswith(displayName,'{query}') or startswith(mail,'{query}')"
                
            r = requests.get(url, headers=headers, params=params)
            if not r.ok:
                return Response({"error": "Failed to fetch users from MS Graph", "details": r.text}, status=r.status_code)
                
            return Response(r.json().get("value", []), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AssignBuddyAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def patch(self, request, id):
        application = get_object_or_404(JobApplication, id=id)
        
        technical_buddy_email = request.data.get('technical_buddy_email')
        technical_buddy_name = request.data.get('technical_buddy_name')
        cultural_buddy_email = request.data.get('cultural_buddy_email')
        cultural_buddy_name = request.data.get('cultural_buddy_name')
        
        update_fields = []
        if technical_buddy_email and technical_buddy_name:
            application.technical_buddy_email = technical_buddy_email
            application.technical_buddy_name = technical_buddy_name
            update_fields.extend(['technical_buddy_email', 'technical_buddy_name'])
        
        if cultural_buddy_email and cultural_buddy_name:
            application.cultural_buddy_email = cultural_buddy_email
            application.cultural_buddy_name = cultural_buddy_name
            update_fields.extend(['cultural_buddy_email', 'cultural_buddy_name'])
            
        application.emp_account_active = True
        if 'emp_account_active' not in update_fields:
            update_fields.append('emp_account_active')
            
        if update_fields:
            application.save(update_fields=update_fields)
        
        # Send buddy emails
        try:
            from onboarding.utils.sender import send_email
            from onboarding.utils.templates import NOTIFY_INTERNAL_HTML_TEMPLATES
            html_template = NOTIFY_INTERNAL_HTML_TEMPLATES.get('buddy_assigned', '<p>Buddy assigned.</p>')
            
            if technical_buddy_email:
                send_email(
                    to=technical_buddy_email,
                    subject="You have been assigned as a Technical Buddy",
                    text="You have been assigned as a Technical Buddy for " + application.candidate_name,
                    template=html_template.format(candidate=application, reciever_name=technical_buddy_name or "Team"),
                    event="buddy_assigned",
                    email_type="internal",
                    candidate=application
                )
            if cultural_buddy_email:
                send_email(
                    to=cultural_buddy_email,
                    subject="You have been assigned as a Cultural Buddy",
                    text="You have been assigned as a Cultural Buddy for " + application.candidate_name,
                    template=html_template.format(candidate=application, reciever_name=cultural_buddy_name or "Team"),
                    event="buddy_assigned",
                    email_type="internal",
                    candidate=application
                )
        except Exception as e:
            print("BUDDY ERROR:", e)
            logger.error(f"Error notifying buddies: {e}")
        
        return Response({"message": "Buddies assigned successfully"}, status=status.HTTP_200_OK)

BINARY_OPTIONS = ["agree", "disagree"]
LIKERT_OPTIONS = ["strongly_agree", "agree", "neutral", "disagree", "strongly_disagree"]
RECOMMEND_OPTIONS = ["yes", "no", "not_sure"]

CANDIDATE_SURVEY_STRUCTURE = {
    "title": "30-Day Onboarding Experience Survey",
    "purpose": "To understand Crafter's onboarding experience and identify opportunities to improve the new hire journey.",
    "rating_info": "Each statement can be rated as: Agree or Disagree.",
    "sections": [
        {
            "id": 1,
            "title": "Section 1: Pre-Joining Experience",
            "questions": [
                {"id": 1, "type": "binary", "text": "The communication provided before my joining date was timely and clear."},
                {"id": 2, "type": "binary", "text": "I received all necessary information before my first day."},
                {"id": 3, "type": "binary", "text": "HR was responsive to my queries during the pre-joining process."},
            ]
        },
        {
            "id": 2,
            "title": "Section 2: Joining Day Experience",
            "questions": [
                {"id": 4, "type": "binary", "text": "My first day was well-organized and welcoming."},
                {"id": 5, "type": "binary", "text": "I had access to the required assets and resources on time."},
                {"id": 6, "type": "binary", "text": "The joining formalities and documentation process were smooth."},
            ]
        },
        {
            "id": 3,
            "title": "Section 3: Role & Expectations",
            "questions": [
                {"id": 7, "type": "binary", "text": "My role and responsibilities were clearly explained."},
                {"id": 8, "type": "binary", "text": "I understand how my work contributes to the team's goals."},
            ]
        },
        {
            "id": 4,
            "title": "Section 4: Training & Support",
            "questions": [
                {"id": 9,  "type": "binary", "text": "The onboarding and training sessions were useful."},
                {"id": 10, "type": "binary", "text": "The training provided was adequate for me to perform my job effectively."},
                {"id": 11, "type": "binary", "text": "I know whom to approach when I need support or guidance."},
                {"id": 12, "type": "binary", "text": "The onboarding materials and resources were helpful."},
            ]
        },
        {
            "id": 5,
            "title": "Section 5: Manager & Team Integration",
            "questions": [
                {"id": 13, "type": "binary", "text": "My manager / Trainers has been available and supportive during my onboarding and training period."},
                {"id": 14, "type": "binary", "text": "I receive regular guidance and feedback from my manager."},
                {"id": 15, "type": "binary", "text": "My team has been welcoming and supportive."},
                {"id": 16, "type": "binary", "text": "I feel comfortable asking questions and seeking help when needed."},
            ]
        },
        {
            "id": 6,
            "title": "Section 6: Culture & Work Environment",
            "questions": [
                {"id": 17, "type": "binary", "text": "I have gained a good understanding of the company's culture and values."},
                {"id": 18, "type": "binary", "text": "I feel included and connected with my team."},
                {"id": 19, "type": "binary", "text": "The work environment supports my learning and growth."},
            ]
        },
        {
            "id": 7,
            "title": "Section 7: Overall Experience",
            "questions": [
                {"id": 20, "type": "binary", "text": "Overall, I am satisfied with my onboarding experience."},
                {"id": 21, "type": "binary", "text": "The organization has helped me settle into my role effectively."},
                {"id": 22, "type": "binary", "text": "I can see myself building a successful career here."},
                {"id": 23, "type": "binary", "text": "I would recommend this organization to prospective employees."},
            ]
        },
        {
            "id": 8,
            "title": "Open-Ended Questions",
            "questions": [
                {"id": 24, "type": "text", "text": "What could we have done differently to improve your onboarding experience?"},
                {"id": 25, "type": "text", "text": "Any other comments or suggestions?"},
            ]
        },
    ],
    "options": {
        "binary": BINARY_OPTIONS,
    }
}

SURVEY_90_DAY_STRUCTURE = {
    "title": "90-Day Onboarding Survey",
    "sections": [
        {
            "id": 1,
            "title": "Role Clarity & Expectations",
            "questions": [
                {"id": 1, "type": "likert", "text": "I clearly understand my role and key responsibilities."},
                {"id": 2, "type": "likert", "text": "My goals and performance expectations were clearly communicated."},
                {"id": 3, "type": "likert", "text": "I understand how my role contributes to the team and organization's objectives."},
            ]
        },
        {
            "id": 2,
            "title": "Training & Resources",
            "questions": [
                {"id": 4, "type": "likert", "text": "The onboarding training prepared me to perform my role effectively."},
                {"id": 5, "type": "likert", "text": "I received timely access to the required tools, systems, and resources."},
                {"id": 6, "type": "likert", "text": "The learning materials and documentation were useful and accessible."},
            ]
        },
        {
            "id": 3,
            "title": "Manager & Team Support",
            "questions": [
                {"id": 7, "type": "likert", "text": "My manager provided adequate guidance and support during my first 90 days."},
                {"id": 8, "type": "likert", "text": "Regular check-ins and feedback helped me adjust to my role."},
                {"id": 9, "type": "likert", "text": "My team has been welcoming, collaborative, and supportive."},
            ]
        },
        {
            "id": 4,
            "title": "Culture & Engagement",
            "questions": [
                {"id": 10, "type": "likert", "text": "I feel welcomed and included in the organization."},
                {"id": 11, "type": "likert", "text": "I understand and align with the company's values and culture."},
                {"id": 12, "type": "likert", "text": "I feel comfortable sharing ideas or asking questions."},
            ]
        },
        {
            "id": 5,
            "title": "Overall Experience",
            "questions": [
                {"id": 13, "type": "likert", "text": "Overall, my onboarding experience met my expectations."},
                {"id": 14, "type": "likert", "text": "I feel confident in my ability to succeed in my role going forward."},
            ]
        },
        {
            "id": 6,
            "title": "Feedback",
            "questions": [
                {"id": 15, "type": "text", "text": "What aspects of the onboarding process worked well for you?"},
                {"id": 16, "type": "text", "text": "What challenges did you face during your first 90 days?"},
                {"id": 17, "type": "text", "text": "What improvements would you suggest for future onboarding programs?"},
                {"id": 18, "type": "text", "text": "Is there any additional support or training you feel would help you perform better?"},
            ]
        },
        {
            "id": 7,
            "title": "Final Question",
            "questions": [
                {"id": 19, "type": "recommend", "text": "Would you recommend this organization as a good place to work based on your onboarding experience?"},
            ]
        },
    ],
    "options": {
        "likert": LIKERT_OPTIONS,
        "recommend": RECOMMEND_OPTIONS,
    }
}


HOD_SURVEY_STRUCTURE_JUNIOR = {
    "title": "HOD Survey (Below Assistant Manager)",
    "sections": [
        {
            "id": 1,
            "title": "Core Assessment",
            "questions": [
                {
                    "id": 1,
                    "type": "binary",
                    "text": "The Crafter has adapted well to the team and work environment."
                },
                {
                    "id": 2,
                    "type": "binary",
                    "text": "The Crafter demonstrates a positive attitude and willingness to learn."
                },
                {
                    "id": 3,
                    "type": "binary",
                    "text": "The Crafter understands their role and responsibilities."
                },
                {
                    "id": 4,
                    "type": "binary",
                    "text": "The Crafter completes assigned tasks effectively and on time."
                },
                {
                    "id": 5,
                    "type": "binary",
                    "text": "The Crafter communicates effectively with colleagues and stakeholders."
                },
                {
                    "id": 6,
                    "type": "binary",
                    "text": "The Crafter collaborates well within the team."
                },
                {
                    "id": 7,
                    "type": "binary",
                    "text": "The onboarding process adequately prepared the Crafter for their role."
                },
                {
                    "id": 8,
                    "type": "binary",
                    "text": "The Crafter aligns with the organization's values and culture."
                },
                {
                    "id": 9,
                    "type": "binary",
                    "text": "Overall, I am satisfied with the Crafter's progress during the initial period."
                }
            ]
        },
        {
            "id": 2,
            "title": "Additional Questions for Junior Crafters",
            "questions": [
                {
                    "id": 10,
                    "type": "binary",
                    "text": "The Crafter actively seeks feedback and applies it to improve performance."
                },
                {
                    "id": 11,
                    "type": "binary",
                    "text": "The Crafter demonstrates eagerness to learn new skills and processes."
                },
                {
                    "id": 12,
                    "type": "binary",
                    "text": "The Crafter asks relevant questions when clarification is needed."
                },
                {
                    "id": 13,
                    "type": "binary",
                    "text": "The Crafter shows the ability to work independently on basic tasks."
                },
                {
                    "id": 14,
                    "type": "binary",
                    "text": "The Crafter effectively follows established processes and guidelines."
                },
                {
                    "id": 15,
                    "type": "binary",
                    "text": "The Crafter demonstrates growth in knowledge and capability since joining."
                },
                {
                    "id": 16,
                    "type": "binary",
                    "text": "The Crafter is open to coaching and mentoring."
                },
                {
                    "id": 17,
                    "type": "binary",
                    "text": "The Crafter takes ownership of assigned work and follows through on commitments."
                },
                {
                    "id": 18,
                    "type": "binary",
                    "text": "The Crafter demonstrates the required foundational technical/professional skills for the role."
                }
            ]
        },
        {
            "id": 3,
            "title": "Open-Ended Questions",
            "questions": [
                {
                    "id": 19,
                    "type": "text",
                    "text": "What are the Crafter's key strengths?"
                },
                {
                    "id": 20,
                    "type": "text",
                    "text": "What areas require further development?"
                },
                {
                    "id": 21,
                    "type": "text",
                    "text": "What support or training would help the Crafter succeed?"
                },
                {
                    "id": 22,
                    "type": "text",
                    "text": "Are there any concerns regarding the Crafter's performance or behavior?"
                },
                {
                    "id": 23,
                    "type": "text",
                    "text": "Additional comments or recommendations."
                }
            ]
        }
    ],
    "options": {
        "binary": [
            "agree",
            "disagree"
        ]
    }
}

HOD_SURVEY_STRUCTURE_SENIOR = {
    "title": "HOD Survey (Assistant Manager and Above)",
    "sections": [
        {
            "id": 1,
            "title": "Core Assessment",
            "questions": [
                {
                    "id": 1,
                    "type": "binary",
                    "text": "The Crafter has adapted well to the team and work environment."
                },
                {
                    "id": 2,
                    "type": "binary",
                    "text": "The Crafter demonstrates a positive attitude and willingness to learn."
                },
                {
                    "id": 3,
                    "type": "binary",
                    "text": "The Crafter understands their role and responsibilities."
                },
                {
                    "id": 4,
                    "type": "binary",
                    "text": "The Crafter completes assigned tasks effectively and on time."
                },
                {
                    "id": 5,
                    "type": "binary",
                    "text": "The Crafter communicates effectively with colleagues and stakeholders."
                },
                {
                    "id": 6,
                    "type": "binary",
                    "text": "The Crafter collaborates well within the team."
                },
                {
                    "id": 7,
                    "type": "binary",
                    "text": "The onboarding process adequately prepared the Crafter for their role."
                },
                {
                    "id": 8,
                    "type": "binary",
                    "text": "The Crafter aligns with the organization's values and culture."
                },
                {
                    "id": 9,
                    "type": "binary",
                    "text": "Overall, I am satisfied with the Crafter's progress during the initial period."
                }
            ]
        },
        {
            "id": 2,
            "title": "Additional Questions for Senior Crafters",
            "questions": [
                {
                    "id": 10,
                    "type": "binary",
                    "text": "The Crafter demonstrates strong leadership and accountability."
                },
                {
                    "id": 11,
                    "type": "binary",
                    "text": "The Crafter effectively mentors and supports team members."
                },
                {
                    "id": 12,
                    "type": "binary",
                    "text": "The Crafter takes initiative in identifying and solving problems."
                },
                {
                    "id": 13,
                    "type": "binary",
                    "text": "The Crafter contributes to strategic discussions and decision-making."
                },
                {
                    "id": 14,
                    "type": "binary",
                    "text": "The Crafter effectively manages stakeholder expectations."
                },
                {
                    "id": 15,
                    "type": "binary",
                    "text": "The Crafter drives collaboration across teams and functions."
                },
                {
                    "id": 16,
                    "type": "binary",
                    "text": "The Crafter demonstrates expertise in their technical/professional domain."
                },
                {
                    "id": 17,
                    "type": "binary",
                    "text": "The Crafter identifies opportunities for process improvement and innovation."
                },
                {
                    "id": 18,
                    "type": "binary",
                    "text": "The Crafter makes sound decisions with minimal supervision."
                },
                {
                    "id": 19,
                    "type": "binary",
                    "text": "The Crafter positively influences team performance and culture."
                },
                {
                    "id": 20,
                    "type": "binary",
                    "text": "The Crafter effectively balances operational responsibilities with long-term objectives."
                }
            ]
        },
        {
            "id": 3,
            "title": "Open-Ended Questions",
            "questions": [
                {
                    "id": 21,
                    "type": "text",
                    "text": "What are the Crafter's key strengths?"
                },
                {
                    "id": 22,
                    "type": "text",
                    "text": "What areas require further development?"
                },
                {
                    "id": 23,
                    "type": "text",
                    "text": "What support or training would help the Crafter succeed?"
                },
                {
                    "id": 24,
                    "type": "text",
                    "text": "Are there any concerns regarding the Crafter's performance or behavior?"
                },
                {
                    "id": 25,
                    "type": "text",
                    "text": "Additional comments or recommendations."
                }
            ]
        }
    ],
    "options": {
        "binary": [
            "agree",
            "disagree"
        ]
    }
}

class GetSurveyStructureAPI(APIView):
    """Returns the full survey form structure for the frontend to render."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        application = get_object_or_404(JobApplication, id=id)
        survey_type = request.query_params.get('survey_type', '30_day_candidate')

        # Check if already submitted
        from onboarding.models import SurveyResponse
        existing = SurveyResponse.objects.filter(
            job_application=application,
            survey_type=survey_type
        ).first()

        # Choose correct structure
        if survey_type == '30_day_candidate':
            structure = CANDIDATE_SURVEY_STRUCTURE
        elif survey_type == 'hod':
            is_senior = False
            if hasattr(application.job, 'mrf') and application.job.mrf and application.job.mrf.designation:
                designation_name = application.job.mrf.designation.name.lower()
                higher_keywords = [
                    'assistant manager', 'associate manager', 'manager', 
                    'senior manager', 'associate vice president', 
                    'director', 'vp', 'vice president', 'president', 
                    'head', 'chief', 'lead', 'principal', 'avp'
                ]
                for kw in higher_keywords:
                    if kw in designation_name:
                        is_senior = True
                        break
            
            if is_senior:
                structure = HOD_SURVEY_STRUCTURE_SENIOR
            else:
                structure = HOD_SURVEY_STRUCTURE_JUNIOR
        else:
            structure = SURVEY_90_DAY_STRUCTURE

        return Response({
            "survey_type": survey_type,
            "candidate_name": application.candidate_name,
            "role": application.job.mrf.designation.name if hasattr(application.job, 'mrf') and application.job.mrf else "",
            "department": application.job.mrf.department.name if hasattr(application.job, 'mrf') and application.job.mrf else "",
            "date_of_joining": application.joining_date,
            "already_submitted": existing is not None and bool(existing.responses),
            "submitted_at": existing.submitted_at if (existing and bool(existing.responses)) else None,
            "structure": structure,
        })

class CompleteSurveyAPI(APIView):
    permission_classes = [permissions.AllowAny]
    def patch(self, request, id):
        application = get_object_or_404(JobApplication, id=id)
        survey_type = request.data.get('survey_type', '30_day_candidate')

        responses_data = request.data.get('responses', {})

        # ── Respondent: auto-fill from DB for candidate surveys; require for HOD ──
        if survey_type in ('30_day_candidate', '90_day_candidate'):
            respondent_name = application.candidate_name or ''
            respondent_email = getattr(application, 'work_email', None) or application.candidate_email or ''
        else:
            # HOD survey — must be supplied in the request body
            respondent_name = request.data.get('respondent_name', '').strip()
            respondent_email = request.data.get('respondent_email', '').strip()
            if not respondent_name or not respondent_email:
                return Response(
                    {"error": "respondent_name and respondent_email are required for HOD surveys."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if not isinstance(responses_data, dict):
            return Response({"error": "'responses' must be a JSON object."}, status=status.HTTP_400_BAD_REQUEST)


        errors = {}

        if survey_type == '30_day_candidate':
            # ── Validate binary questions (Q1–Q23) ──────────────────────────
            binary_qids = list(range(1, 24))
            for qid in binary_qids:
                key = str(qid)
                val = responses_data.get(key)
                if val is None:
                    errors[key] = f"Q{qid} is required."
                elif val not in BINARY_OPTIONS:
                    errors[key] = f"Q{qid}: must be one of {BINARY_OPTIONS}."
            # ── Text questions (Q24–Q25) are optional ────────────────────────
            for qid in [24, 25]:
                key = str(qid)
                val = responses_data.get(key)
                if val is not None and not isinstance(val, str):
                    errors[key] = f"Q{qid}: must be a text string."
        
        elif survey_type == 'hod':
            # ── Determine if Senior or Junior ────────────────────────────────
            is_senior = False
            if hasattr(application.job, 'mrf') and application.job.mrf and application.job.mrf.designation:
                designation_name = application.job.mrf.designation.name.lower()
                higher_keywords = [
                    'assistant manager', 'associate manager', 'manager', 
                    'senior manager', 'associate vice president', 
                    'director', 'vp', 'vice president', 'president', 
                    'head', 'chief', 'lead', 'principal', 'avp'
                ]
                for kw in higher_keywords:
                    if kw in designation_name:
                        is_senior = True
                        break
            
            binary_count = 20 if is_senior else 18
            text_start = binary_count + 1
            text_end = binary_count + 5
            
            # ── Validate binary questions ────────────────────────────────────
            for qid in range(1, binary_count + 1):
                key = str(qid)
                val = responses_data.get(key)
                if val is None:
                    errors[key] = f"Q{qid} is required."
                elif val not in BINARY_OPTIONS:
                    errors[key] = f"Q{qid}: must be one of {BINARY_OPTIONS}."
                    
            # ── Text questions are optional ──────────────────────────────────
            for qid in range(text_start, text_end + 1):
                key = str(qid)
                val = responses_data.get(key)
                if val is not None and not isinstance(val, str):
                    errors[key] = f"Q{qid}: must be a text string."
                    
        else: # 90_day_candidate
            # ── Validate likert questions (Q1–Q14) ──────────────────────────────
            likert_qids = list(range(1, 15))
            for qid in likert_qids:
                key = str(qid)
                val = responses_data.get(key)
                if val is None:
                    errors[key] = f"Q{qid} is required."
                elif val not in LIKERT_OPTIONS:
                    errors[key] = f"Q{qid}: must be one of {LIKERT_OPTIONS}."

            # ── Validate recommend question (Q19) ───────────────────────────────
            val19 = responses_data.get("19")
            if val19 is None:
                errors["19"] = "Q19 is required."
            elif val19 not in RECOMMEND_OPTIONS:
                errors["19"] = f"Q19: must be one of {RECOMMEND_OPTIONS}."

            # ── Text questions (Q15–Q18) are optional, just ensure strings ──────
            for qid in range(15, 19):
                key = str(qid)
                val = responses_data.get(key)
                if val is not None and not isinstance(val, str):
                    errors[key] = f"Q{qid}: must be a text string."

        if errors:
            return Response({"error": "Validation failed.", "fields": errors}, status=status.HTTP_400_BAD_REQUEST)

        # ── Uniqueness guard: block re-submissions ────────────────────────────
        from onboarding.models import SurveyResponse
        existing = SurveyResponse.objects.filter(
            job_application=application,
            survey_type=survey_type
        ).first()

        if existing and existing.responses:
            return Response(
                {
                    "error": "Survey already submitted.",
                    "already_submitted": True,
                    "submitted_at": existing.submitted_at,
                },
                status=status.HTTP_409_CONFLICT
            )

        # ── Persist ─────────────────────────────────────────────────────────
        SurveyResponse.objects.update_or_create(
            job_application=application,
            survey_type=survey_type,
            defaults={
                'respondent_name': respondent_name,
                'respondent_email': respondent_email,
                'responses': responses_data,
            }
        )

        # ── Update completion flag based on survey type ───────────────────────
        if survey_type == 'hod':
            application.is_hod_survey_filled = True
            application.save(update_fields=['is_hod_survey_filled'])
        elif survey_type == '90_day_candidate':
            application.is_d90_survey_filled = True
            application.save(update_fields=['is_d90_survey_filled'])
        else:
            # Default: 30-day candidate survey
            application.is_satisfaction_survey_filled = True
            application.save(update_fields=['is_satisfaction_survey_filled'])

        return Response({"message": "Survey submitted successfully."}, status=status.HTTP_200_OK)

class ScheduleD45CallAPI(APIView):
    permission_classes = [permissions.AllowAny]
    def patch(self, request, id):
        application = get_object_or_404(JobApplication, id=id)
        
        organizer_email = request.data.get('organizer_email')
        start_time_str = request.data.get('start_time')
        end_time_str = request.data.get('end_time')
        # Extra attendees beyond the candidate (e.g. HR, HOD)
        attendee_emails = request.data.get('attendee_emails', [])
        if isinstance(attendee_emails, str):
            attendee_emails = [attendee_emails]
            
        from django.conf import settings
        if getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False):
            organizer_email = "harshil@jmstech.co"
            attendee_emails.extend(["zeelsh@jmstech.co", "anand@jmstech.co"])
        
        if organizer_email and start_time_str and end_time_str:
            try:
                from dateutil.parser import parse
                from booking.utils import create_teams_meeting, update_teams_meeting
                from onboarding.models import OnboardingCall
                
                start_dt = parse(start_time_str)
                end_dt = parse(end_time_str)
                candidate_email = application.work_email or application.candidate_email
                subject = f"Day 45 Check-in Call: {application.candidate_name}"
                
                # Build deduplicated attendee list: candidate first, then extras
                all_attendees = [candidate_email] + [
                    e for e in attendee_emails if e and e != candidate_email
                ]
                
                # Check if a meeting already exists for this candidate
                existing_call = OnboardingCall.objects.filter(
                    job_application=application, call_type="d45"
                ).first()
                
                if existing_call and existing_call.meeting_id:
                    # ── UPDATE the existing Teams calendar event (no duplicate created) ──
                    event = update_teams_meeting(
                        organizer_email=organizer_email,
                        event_id=existing_call.meeting_id,
                        start_dt=start_dt,
                        end_dt=end_dt,
                        subject=subject,
                    )
                    meeting_id = existing_call.meeting_id
                    meeting_link = existing_call.meeting_link  # link stays the same
                else:
                    # ── CREATE a fresh Teams meeting ──
                    event = create_teams_meeting(
                        organizer_email, all_attendees, start_dt, end_dt, subject
                    )
                    meeting_id = event.get("id") if event else None
                    meeting_link = (
                        (event.get("onlineMeeting") or {}).get("joinUrl")
                        or event.get("onlineMeetingUrl")
                        or (event.get("onlineMeeting") or {}).get("joinWebUrl")
                        or None
                    ) if event else None
                
                # Persist / update the DB record
                OnboardingCall.objects.update_or_create(
                    job_application=application,
                    call_type="d45",
                    defaults={
                        "organizer_email": organizer_email,
                        "start_time": start_dt,
                        "end_time": end_dt,
                        "meeting_id": meeting_id,
                        "meeting_link": meeting_link,
                    }
                )
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating/updating Teams meeting for D45: {e}")
                return Response({"error": f"Failed to book MS Teams meeting: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
                
        application.is_d45_call_scheduled = True
        application.save(update_fields=['is_d45_call_scheduled'])     
        return Response({"message": "Day 45 check-in call booked and marked as scheduled"}, status=status.HTTP_200_OK)

class ScheduleD90CallAPI(APIView):
    permission_classes = [permissions.AllowAny]
    def patch(self, request, id):
        application = get_object_or_404(JobApplication, id=id)
        
        organizer_email = request.data.get('organizer_email')
        start_time_str = request.data.get('start_time')
        end_time_str = request.data.get('end_time')
        # Extra attendees beyond the candidate (e.g. HR, HOD)
        attendee_emails = request.data.get('attendee_emails', [])
        if isinstance(attendee_emails, str):
            attendee_emails = [attendee_emails]
            
        from django.conf import settings
        if getattr(settings, 'ONBOARDING_DEBUG_MINUTES', False):
            organizer_email = "harshil@jmstech.co"
            attendee_emails.extend(["zeelsh@jmstech.co", "anand@jmstech.co"])
        
        if organizer_email and start_time_str and end_time_str:
            try:
                from dateutil.parser import parse
                from booking.utils import create_teams_meeting, update_teams_meeting
                from onboarding.models import OnboardingCall
                
                start_dt = parse(start_time_str)
                end_dt = parse(end_time_str)
                candidate_email = application.work_email or application.candidate_email
                subject = f"Day 90 Final Review Call: {application.candidate_name}"
                
                # Build deduplicated attendee list: candidate first, then extras
                all_attendees = [candidate_email] + [
                    e for e in attendee_emails if e and e != candidate_email
                ]
                
                # Check if a meeting already exists for this candidate
                existing_call = OnboardingCall.objects.filter(
                    job_application=application, call_type="d90"
                ).first()
                
                if existing_call and existing_call.meeting_id:
                    # ── UPDATE the existing Teams calendar event (no duplicate created) ──
                    event = update_teams_meeting(
                        organizer_email=organizer_email,
                        event_id=existing_call.meeting_id,
                        start_dt=start_dt,
                        end_dt=end_dt,
                        subject=subject,
                    )
                    meeting_id = existing_call.meeting_id
                    meeting_link = existing_call.meeting_link  # link stays the same
                else:
                    # ── CREATE a fresh Teams meeting ──
                    event = create_teams_meeting(
                        organizer_email, all_attendees, start_dt, end_dt, subject
                    )
                    meeting_id = event.get("id") if event else None
                    meeting_link = (
                        (event.get("onlineMeeting") or {}).get("joinUrl")
                        or event.get("onlineMeetingUrl")
                        or (event.get("onlineMeeting") or {}).get("joinWebUrl")
                        or None
                    ) if event else None
                
                # Persist / update the DB record
                OnboardingCall.objects.update_or_create(
                    job_application=application,
                    call_type="d90",
                    defaults={
                        "organizer_email": organizer_email,
                        "start_time": start_dt,
                        "end_time": end_dt,
                        "meeting_id": meeting_id,
                        "meeting_link": meeting_link,
                    }
                )
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating/updating Teams meeting for D90: {e}")
                return Response({"error": f"Failed to book MS Teams meeting: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        application.is_d90_call_scheduled = True
        application.save(update_fields=['is_d90_call_scheduled'])
        return Response({"message": "Day 90 final review call booked and marked as scheduled"}, status=status.HTTP_200_OK)

class OnboardingJourneyAPI(APIView):
    """
    GET /api/onboarding/application/<id>/journey/

    Returns a consolidated snapshot of the candidate's end-to-end onboarding
    journey — from initialization through to Day 90 — including:
      • Candidate & role details
      • MRF / Requisition details
      • Key milestone dates and completion flags
      • D45 / D90 call schedule data
      • All survey responses enriched with question text
      • Onboarding task lists and their tasks
      • IT ticket and buddy info
    """
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def _build_question_map(structure):
        """Flatten survey structure sections into {str(qid): (section_title, question_text)}."""
        qmap = {}
        for section in structure.get("sections", []):
            section_title = section.get("title", "")
            for q in section.get("questions", []):
                qmap[str(q["id"])] = (section_title, q["text"])
        return qmap

    @staticmethod
    def _enrich_responses(raw_responses, question_map):
        """Convert {str(id): answer} to [{question_id, section, question, answer}] in survey order."""
        enriched = []
        for qid, (section_title, question_text) in question_map.items():
            enriched.append({
                "question_id": int(qid),
                "section": section_title,
                "question": question_text,
                "answer": raw_responses.get(qid),
            })
        return enriched

    def get(self, request, id):
        from onboarding.models import OnboardingCall, SurveyResponse, OnboardingTaskList, DocumentEsignTask
        from django.utils import timezone as tz

        application = get_object_or_404(JobApplication, id=id)
        today = tz.now().date()

        # ── Days since joining ─────────────────────────────────────────────
        joining_date = application.joining_date
        days_since_joining = (today - joining_date).days if joining_date else None

        # ── MRF / Requisition details ──────────────────────────────────────
        mrf_data = None
        is_senior = False
        try:
            if application.job and application.job.mrf:
                mrf = application.job.mrf
                designation_name = mrf.designation.name if mrf.designation else ""
                higher_keywords = [
                    'assistant manager', 'associate manager', 'manager',
                    'senior manager', 'associate vice president',
                    'director', 'vp', 'vice president', 'president',
                    'head', 'chief', 'lead', 'principal', 'avp'
                ]
                is_senior = any(kw in designation_name.lower() for kw in higher_keywords)
                mrf_data = {
                    "id": str(mrf.id),
                    "requisition_no": mrf.requisition_no,
                    "mrf_name": mrf.mrf_name,
                    "designation": designation_name,
                    "department": mrf.department.name if mrf.department else "",
                    "position_department": mrf.position_department.name if mrf.position_department else "",
                    "team": mrf.team,
                    "location": mrf.location,
                    "job_type": mrf.job_type,
                    "no_of_vacancies": mrf.no_of_vacancies,
                    "experience_range": mrf.experience_range,
                    "salary_range": mrf.salary_range,
                    "status": mrf.status,
                    "priority": mrf.priority,
                    "requested_by_name": mrf.requested_by_name,
                    "requested_by_designation": mrf.requested_by_designation,
                    "date_of_request": mrf.date_of_request,
                    "expected_date_of_joining": mrf.expected_date_of_joining,
                }
        except Exception:
            pass

        # ── Onboarding calls ───────────────────────────────────────────────
        def serialize_call(call):
            if not call:
                return None
            return {
                "id": str(call.id),
                "organizer_email": call.organizer_email,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "meeting_id": call.meeting_id,
                "meeting_link": call.meeting_link,
                "created_at": call.created_at,
            }

        d45_call = OnboardingCall.objects.filter(
            job_application=application, call_type="d45"
        ).first()
        d90_call = OnboardingCall.objects.filter(
            job_application=application, call_type="d90"
        ).first()

        # ── Survey enrichment ──────────────────────────────────────────────
        hod_structure = HOD_SURVEY_STRUCTURE_SENIOR if is_senior else HOD_SURVEY_STRUCTURE_JUNIOR
        structure_map = {
            "30_day_candidate": CANDIDATE_SURVEY_STRUCTURE,
            "hod":              hod_structure,
            "90_day_candidate": SURVEY_90_DAY_STRUCTURE,
        }

        def serialize_survey(survey, survey_type):
            if not survey:
                return None
            raw = survey.responses or {}
            structure = structure_map.get(survey_type, {})
            qmap = self._build_question_map(structure)
            enriched = self._enrich_responses(raw, qmap) if raw else []
            return {
                "id": str(survey.id),
                "survey_type": survey_type,
                "survey_title": structure.get("title", ""),
                "respondent_name": survey.respondent_name,
                "respondent_email": survey.respondent_email,
                "is_submitted": bool(raw),
                "submitted_at": survey.submitted_at,
                "responses": enriched,
            }

        surveys_qs = SurveyResponse.objects.filter(job_application=application)
        survey_map = {s.survey_type: s for s in surveys_qs}

        # ── Task lists & tasks ─────────────────────────────────────────────
        task_lists = OnboardingTaskList.objects.filter(
            job_application=application
        ).prefetch_related("tasks")

        task_data = []
        for tl in task_lists:
            tasks = []
            for t in tl.tasks.all():
                tasks.append({
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "assigned_to": t.assigned_to.get_full_name() if t.assigned_to else None,
                    "due_date": t.due_date,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at,
                })
            task_data.append({
                "id": str(tl.id),
                "name": tl.name,
                "description": tl.description,
                "created_at": tl.created_at,
                "tasks": tasks,
            })

        # ── Milestone summary ──────────────────────────────────────────────
        milestones = [
            {
                "key": "onboarding_initiated",
                "label": "Onboarding Initiated",
                "completed": bool(application.it_ticket_ref),
                "detail": f"IT Ticket: {application.it_ticket_ref}" if application.it_ticket_ref else None,
            },
            {
                "key": "joined",
                "label": "Joined",
                "completed": application.status == "joined",
                "detail": str(joining_date) if joining_date else None,
            },
            {
                "key": "d30_survey_sent",
                "label": "Day 30 — Candidate Survey Sent",
                "completed": application.is_d30_survey_sent,
                "detail": None,
            },
            {
                "key": "d30_survey_filled",
                "label": "Day 30 — Candidate Survey Filled",
                "completed": application.is_satisfaction_survey_filled,
                "detail": None,
            },
            {
                "key": "hod_survey_filled",
                "label": "Day 30 — HOD Survey Filled",
                "completed": application.is_hod_survey_filled,
                "detail": None,
            },
            {
                "key": "d45_call_scheduled",
                "label": "Day 45 — Check-in Call Scheduled",
                "completed": application.is_d45_call_scheduled,
                "detail": str(d45_call.start_time) if d45_call and d45_call.start_time else None,
            },
            {
                "key": "d90_survey_sent",
                "label": "Day 90 — Survey Sent",
                "completed": application.is_d90_survey_sent,
                "detail": None,
            },
            {
                "key": "d90_survey_filled",
                "label": "Day 90 — Survey Filled",
                "completed": application.is_d90_survey_filled,
                "detail": None,
            },
            {
                "key": "d90_call_scheduled",
                "label": "Day 90 — Final Review Call Scheduled",
                "completed": application.is_d90_call_scheduled,
                "detail": str(d90_call.start_time) if d90_call and d90_call.start_time else None,
            },
            {
                "key": "it_ticket_closed",
                "label": "IT Ticket Closed",
                "completed": application.it_ticket_closed,
                "detail": None,
            },
        ]

        data = {
            # ── Candidate ────────────────────────────────────────────
            "candidate": {
                "id": str(application.id),
                "name": application.candidate_name,
                "email": application.candidate_email,
                "work_email": application.work_email,
                "phone": application.candidate_phone,
                "status": application.status,
                "joining_date": joining_date,
                "days_since_joining": days_since_joining,
                "is_escalated": application.is_escalated,
                "it_ticket_ref": application.it_ticket_ref,
                "it_ticket_closed": application.it_ticket_closed,
                "emp_account_active": application.emp_account_active,
            },

            # ── MRF / Requisition ────────────────────────────────────
            "mrf": mrf_data,

            # ── Buddies ──────────────────────────────────────────────
            "buddies": {
                "technical_buddy_name": application.technical_buddy_name,
                "technical_buddy_email": application.technical_buddy_email,
                "cultural_buddy_name": application.cultural_buddy_name,
                "cultural_buddy_email": application.cultural_buddy_email,
            },

            # ── E-Sign Docs ──────────────────────────────────────────
            "esign_docs": [
                {
                    "id": str(doc.id),
                    "doc_type": doc.doc_type,
                    "doc_type_display": doc.get_doc_type_display(),
                    "status": doc.status,
                    "status_display": doc.get_status_display(),
                    "zoho_request_id": doc.zoho_request_id,
                    "zoho_document_id": doc.zoho_document_id,
                    "generated_at": doc.generated_at,
                    "sent_at": doc.sent_at,
                    "viewed_at": doc.viewed_at,
                    "signed_at": doc.signed_at,
                    "completed_at": doc.completed_at,
                }
                for doc in DocumentEsignTask.objects.filter(job_application=application).order_by('created_at')
            ],


            # ── Milestones ───────────────────────────────────────────
            "milestones": milestones,

            # ── Calls ────────────────────────────────────────────────
            "calls": {
                "d45": serialize_call(d45_call),
                "d90": serialize_call(d90_call),
            },

            # ── Surveys (enriched Q&A) ───────────────────────────────
            "surveys": {
                "30_day_candidate": serialize_survey(
                    survey_map.get("30_day_candidate"), "30_day_candidate"
                ),
                "hod": serialize_survey(
                    survey_map.get("hod"), "hod"
                ),
                "90_day_candidate": serialize_survey(
                    survey_map.get("90_day_candidate"), "90_day_candidate"
                ),
            },

            # ── Tasks ────────────────────────────────────────────────
            "task_lists": task_data,
        }

        return Response(data, status=status.HTTP_200_OK)


class GetManageEngineSitesAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from .utils.zoho_manageengine import ManageEngineClient
        client = ManageEngineClient()
        sites = client.get_sites()
        return Response({"sites": sites}, status=status.HTTP_200_OK)

class GetManageEngineAssetsAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from .utils.zoho_manageengine import ManageEngineClient
        client = ManageEngineClient()
        assets = client.get_assets()
        return Response({"assets": assets}, status=status.HTTP_200_OK)

class GetManageEngineDepartmentsAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from .utils.zoho_manageengine import ManageEngineClient
        client = ManageEngineClient()
        departments = client.get_departments()
        return Response({"departments": departments}, status=status.HTTP_200_OK)

class GetManageEngineDesignationsAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from .utils.zoho_manageengine import ManageEngineClient
        client = ManageEngineClient()
        designations = client.get_designations()
        return Response({"designations": designations}, status=status.HTTP_200_OK)

class OnboardingTaskListViewSet(ModelViewSet):
    queryset = OnboardingTaskList.objects.all()
    serializer_class = OnboardingTaskListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        job_application_id = self.request.query_params.get('job_application_id')
        
        if job_application_id:
            queryset = queryset.filter(job_application_id=job_application_id)
            
        return queryset

class OnboardingTaskViewSet(ModelViewSet):
    queryset = OnboardingTask.objects.all()
    serializer_class = OnboardingTaskSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        task_list_id = self.request.query_params.get('task_list_id')
        assigned_to_id = self.request.query_params.get('assigned_to_id')
        
        if task_list_id:
            queryset = queryset.filter(task_list_id=task_list_id)
        if assigned_to_id:
            queryset = queryset.filter(assigned_to_id=assigned_to_id)
            
        return queryset

class DocumentEsignTaskViewSet(ModelViewSet):
    queryset = DocumentEsignTask.objects.all()
    serializer_class = DocumentEsignTaskSerializer
    permission_classes = [permissions.AllowAny]
 
    def get_queryset(self):
        queryset = super().get_queryset()
        job_application_id = self.request.query_params.get('job_application_id')
        status_filter = self.request.query_params.get('status')
 
        if job_application_id:
            queryset = queryset.filter(job_application_id=job_application_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
 
        return queryset