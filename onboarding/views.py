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
from .models import JobApplicationDocument,ApprovalNote,SalaryAnnexure,SalaryAnnexureHistory,SalaryComponent
from onboarding.utils.engine import automation_engine
from .utils.sender import send_email,send_text,send_document
from .serializers import JobApplicationDocumentSerializer,SalaryAnnexureSerializer,SalaryAnnexureHistorySerializer
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
            application.save()
            return Response({"success": ok,"status":application.status})
        else:
            return Response({"Error:",reason})

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
            ok,reason = automation_engine(application, application.status, "docs_approved")
            if not ok:
                print(reason)
    elif application.status == "salary_annexure_review" and getattr(docs,'joining_docs_status') == 'approved':
            automation_engine(application, application.status, "approved_annexure")
    elif application.status == "salary_annexure_review" and getattr(docs,'joining_docs_status') not in  ['approved','pending']:
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

        # 🟢 Save uploaded files
        updated = False
        for field in request.FILES:
            approved_field = f"{field}_approved"
            if hasattr(docs, field):
                # Skip file if it's already approved
                if hasattr(docs, approved_field) and getattr(docs, approved_field):
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
            approval_notes = ApprovalNote.objects.filter(created_by=user)

        else:
            # Default: manager sees notes assigned to them
            approval_notes = ApprovalNote.objects.filter(manager=user)

        # Apply privacy filter
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
                        attachments=[resume_attachment] if resume_attachment else None
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
        approval_note.save()

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
                attachments=[annexure_attachment] if annexure_attachment else None
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
                attachments=[resume_attachment] if resume_attachment else None
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