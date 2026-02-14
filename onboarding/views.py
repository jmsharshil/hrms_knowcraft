# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from .models import JobApplicationDocument,ApprovalNote,SalaryAnnexure,SalaryAnnexureHistory,SalaryComponent
from onboarding.utils.engine import automation_engine
from .utils.sender import send_email
from .serializers import JobApplicationDocumentSerializer,SalaryAnnexureSerializer,SalaryAnnexureHistorySerializer
import logging
from jobs.models import JobApplication
from rest_framework.viewsets import ModelViewSet,ReadOnlyModelViewSet
from .utils.annexure_history import log_salary_annexure_history
logger = logging.getLogger(__name__)


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
                interviewer_email = application.job.mrf.interviewer_email_1
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
                application.slot_link = f"https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net/api/slots/available/?candidate_id={application.id}&interviewer_id={interviewer_id}"
            else:
                interviewer_id = None
                application.slot_link = ""
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

    # Salary stage
    if application.status in ["salary_docs_uploaded","hr_review_docs","salary_docs_unclear","salary_docs_incomplete"]:
        if is_section_unclear(docs,"salary"):
            automation_engine(application, application.status, "salary_docs_unclear")
        elif is_section_incomplete(docs,"salary"):
            automation_engine(application, application.status, "salary_docs_incomplete")
        elif is_section_complete(docs, "salary"):
            automation_engine(application, application.status, "hr_review_ok")

    # Resignation stage
    elif application.status in ["resignation_uploaded","resignation_review","resignation_incomplete","resignation_unclear"]:
        if is_section_unclear(docs,"resignation"):
            automation_engine(application, application.status, "resignation_unclear")
        elif is_section_incomplete(docs,"resignation"):
            automation_engine(application, application.status, "resignation_incomplete")
        elif is_section_complete(docs, "resignation"):
            automation_engine(application, application.status, "resignation_approved")

    # Joining documents stage
    elif application.status in ["docs_uploaded","review_docs","docs_unclear","docs_incomplete"]:
        if is_section_incomplete(docs, "joining_docs"):
            automation_engine(application, application.status, "docs_incomplete")
        elif is_section_unclear(docs, "joining_docs"):
            automation_engine(application, application.status, "docs_unclear")
        elif is_section_complete(docs, "joining_docs"):
            automation_engine(application, application.status, "docs_approved")

class UploadJobApplicationDocumentAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, id):
        application = get_object_or_404(JobApplication, id=id)

        docs, _ = JobApplicationDocument.objects.get_or_create(
            job_application=application
        )


        SECTION_FIELDS = {
            "salary": ["salary_slip_1", "salary_slip_2", "salary_slip_3", "bank_statement"],
            "joining_docs": {
            "personal": ["aadhaar", "pan", "passport", "photograph", "address_proof"],
            "education": [
                "tenth_certificate",
                "twelfth_certificate",
                "graduation_certificate",
                "post_graduation_certificate",
            ],
            "experience": [
                "experience_letter_1",
                "experience_letter_2",
                "relieving_letter",
            ]},
            "resignation": ["resignation_letter", "resignation_acceptance"],
        }

        for section, fields in SECTION_FIELDS.items():
            if getattr(docs, f"{section}_status") == "approved":
                for field in fields:
                    if field in request.FILES:
                        return Response(
                            {"error": f"{section} documents already approved"},
                            status=400
                        )

        # 🟢 Save uploaded files
        updated = False
        for field in request.FILES:
            if hasattr(docs, field):
                setattr(docs, field, request.FILES[field])
                updated = True

        if not updated:
            return Response({"error": "Invalid document field"}, status=400)

        docs.save()

        if application.status == "salary_docs_pending":
            automation_engine(application, "salary_docs_pending", "salary_docs_uploaded")

        elif application.status == "resignation_pending":
            automation_engine(application, "resignation_pending", "resignation_uploaded")

        elif application.status == "docs_pending":
            automation_engine(application, "docs_pending", "docs_uploaded")

        return Response(
            {
                "message": "Documents uploaded successfully",
                "documents": JobApplicationDocumentSerializer(docs).data,
            },
            status=200
        )

class ReviewJobApplicationDocumentsAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        docs = get_object_or_404(
            JobApplicationDocument,
            job_application_id=id
        )

        section = request.data.get("section")
        status_value = request.data.get("status")
        remarks = request.data.get("remarks")

        if section not in [
            "salary", "personal", "education", "experience", "resignation","joining_docs"
        ]:
            return Response({"error": "Invalid section"}, status=400)

        # 🔒 Lock rule
        if getattr(docs, f"{section}_status") == "approved":
            return Response(
                {"error": f"{section} already approved"},
                status=400
            )

        setattr(docs, f"{section}_status", status_value)
        setattr(docs, f"{section}_remarks", remarks)
        docs.save()

        # 🔁 Evaluate partial approval logic
        evaluate_documents(docs.job_application)

        return Response({
            "message": f"{section} documents updated",
            "status": status_value
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

        approval_notes = approval_notes.select_related("candidate")

        results = []

        for note in approval_notes:
            results.append({
                "approval_note_id": str(note.id),
                "candidate_id": str(note.candidate.id),
                "status": note.status,
                "created_at": note.created_at,
                "data": note.payload
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

        # --- Resolve relations ---
        mrf = candidate.job.mrf
        department = mrf.department
        designation = mrf.designation
        approver = mrf.requested_by
        requested_by_name = request.user.name
        requested_by_email = request.user.email
        requested_by_role = request.user.role

        # --- HTML Template ---
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; color:#333; line-height:1.6;">
            <h2 style="color:#2c3e50;">Approval Required – Candidate Hiring</h2>

            <p>Dear <strong>{{ approver_name }}</strong>,</p>

            <p>
            Sharing the formal approval note regarding 
            <strong>{{ candidate_name }}</strong> shortlisted as 
            <strong>{{ designation }}</strong> – <strong>{{ department }}</strong>.
            </p>

            <table style="border-collapse: collapse; width:100%; margin-top:15px;">
                <tr><td><strong>Name of Candidate</strong></td><td>{{ candidate_name }}</td></tr>
                <tr><td><strong>Designation</strong></td><td>{{ designation }}</td></tr>
                <tr><td><strong>Experience</strong></td><td>{{ experience }}</td></tr>
                <tr><td><strong>Qualification</strong></td><td>{{ qualification }}</td></tr>
                <tr><td><strong>Last Organization</strong></td><td>{{ last_organization }}</td></tr>

                <tr><td colspan="2"><br><strong>Interviewers</strong></td></tr>
                <tr><td>HR Round</td><td>{{ hr_round_interviewer }}</td></tr>
                <tr><td>Technical Round</td><td>{{ tech_round_interviewer }}</td></tr>
                <tr><td>Case Study Round</td><td>{{ case_study_round_interviewer }}</td></tr>
                <tr><td>Final Round</td><td>{{ final_round_interviewer }}</td></tr>
                <tr><td>Management/Client Round</td><td>{{ management_client_round_interviewer }}</td></tr>

                <tr><td colspan="2"><br><strong>Scores</strong></td></tr>
                <tr><td>HR Round</td><td>{{ hr_round_score }}</td></tr>
                <tr><td>Technical Round</td><td>{{ tech_round_score }}</td></tr>
                <tr><td>Case Study Round</td><td>{{ case_study_round_score }}</td></tr>
                <tr><td>Final Round</td><td>{{ final_round_score }}</td></tr>
                <tr><td>Management/Client Round</td><td>{{ management_client_round_score }}</td></tr>

                <tr><td><strong>Current / Last Drawn CTC</strong></td><td>{{ current_ctc }}</td></tr>
                <tr><td><strong>Expected CTC</strong></td><td>{{ expected_ctc }}</td></tr>
                <tr><td><strong>CTC to be Offered</strong></td><td>{{ offered_ctc }}</td></tr>
                <tr><td><strong>Notice Period</strong></td><td>{{ notice_period }}</td></tr>
                <tr><td><strong>Office Location</strong></td><td>{{ office_location }}</td></tr>
                <tr><td><strong>Source</strong></td><td>{{ source }}</td></tr>
                <tr><td><strong>MRF</strong></td><td>{{ mrf }}</td></tr>
                <tr><td><strong>New / Replacement</strong></td><td>{{ hiring_type }}</td></tr>

                {% if remarks %}
                <tr><td><strong>Remarks</strong></td><td>{{ remarks }}</td></tr>
                {% endif %}
            </table>

            <p style="margin-top:20px;">
                Request you to review the same and share your feedback, if any.
            </p>

            <p>
                Regards,<br>
                <strong>{{ hr_name }}</strong><br>
                Recruitment Team
            </p>
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
        }

        # --- Render email ---
        template = Template(html_content)
        html_rendered = template.render(Context(context))

        # --- Trigger workflow ---
        try:
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
                # --- Send email ---
                send_email(
                    subject="Approval Required – Candidate Hiring",
                    text="Approval required. Please view this email in HTML format.",
                    to=approver.email,
                    template=html_rendered
                )
            else:
                print(reason)

        except Exception as e:
            print(f"Unable to send the Approval Note:{e}")

        return Response(
            {"status": "Approval note sent successfully"},
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

    def perform_create(self, serializer):
        annexure = serializer.save(prepared_by=self.request.user)
        log_salary_annexure_history(
            annexure,
            action="created",
            user=self.request.user
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
        automation_engine(app, app.status, "salary_annexure_sent")
        log_salary_annexure_history(
            annexure,
            action="sent",
            user=request.user
        )

        return Response({"message": "Salary annexure sent for approval"})

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
        automation_engine(app, app.status, "approved_annexure")
        log_salary_annexure_history(
            annexure,
            action="approved",
            user=request.user
        )

        return Response({"message": "Salary annexure approved"})

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
        automation_engine(app, app.status, "rejected_annexure")
        log_salary_annexure_history(
            annexure,
            action="rejected",
            user=request.user,
            remarks=annexure.rejection_reason
        )

        return Response({"message": "Salary annexure rejected"})

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
        automation_engine(app, app.status, "salary_annexure_prep")
        log_salary_annexure_history(
            annexure,
            action="revised",
            user=request.user,
            remarks=annexure.notes
        )

        return Response(
            {
                "message": "Salary annexure revised successfully",
                "revision_count": annexure.revision_count
            },
            status=status.HTTP_200_OK
        )
    
class SalaryAnnexureHistoryViewSet(ReadOnlyModelViewSet):
    serializer_class = SalaryAnnexureHistorySerializer

    def get_queryset(self):
        """
        Filter by annexure or job application
        """
        qs = SalaryAnnexureHistory.objects.select_related(
            "annexure",
            "performed_by"
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