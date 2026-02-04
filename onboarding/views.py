# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from .models import JobApplicationDocument
from onboarding.utils.engine import automation_engine
from .utils.sender import send_email
from .serializers import JobApplicationDocumentSerializer
import logging
from jobs.models import JobApplication
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
    

class UploadJobApplicationDocumentAPI(APIView):
    permission_classes = [permissions.AllowAny]  # if public for candidate
    
    def post(self, request,id):
        application = get_object_or_404(JobApplication, id=id)

        files = request.FILES.getlist("files")
        doc_type = request.data.get("doc_type", None)

        if not files:
            return Response({"error": "No file uploaded"}, status=400)

        saved_docs = []

        for f in files:
            doc = JobApplicationDocument.objects.create(
                job_application=application,
                file=f,
                doc_type=doc_type
            )
            saved_docs.append(JobApplicationDocumentSerializer(doc).data)

        # OPTIONAL: When first doc uploaded → move to docs_received
        if application.status == "docs_pending":
            ok, reason = automation_engine(application, "docs_pending", "docs_uploaded")
            if not ok:
                return Response({"error": reason}, status=400)
        elif application.status == "salary_docs_pending":
            ok, reason = automation_engine(application, "salary_docs_pending", "salary_docs_uploaded")
            if not ok:
                return Response({"error": reason}, status=400)
        elif application.status == "resignation_pending":
            ok, reason = automation_engine(application, "resignation_pending", "resignation_uploaded")
            if not ok:
                return Response({"error": reason}, status=400)

        return Response({
            "message": "Documents uploaded successfully.",
            "documents": saved_docs
        }, status=201)

class SendApprovalNoteAPIView(APIView):
    """
    Sends approval note email to manager for candidate hiring
    """
    permission_classes = [permissions.IsAuthenticated]
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
        manager = mrf.requested_by
        hr = request.user

        # --- HTML Template ---
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; color:#333; line-height:1.6;">
            <h2 style="color:#2c3e50;">Approval Required – Candidate Hiring</h2>

            <p>Dear <strong>{{ manager_name }}</strong>,</p>

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
                <tr><td>HR Round</td><td>{{ hr_interviewer }}</td></tr>
                <tr><td>Technical Round</td><td>{{ tech_interviewer }}</td></tr>
                <tr><td>Final Round</td><td>{{ final_interviewer }}</td></tr>

                <tr><td colspan="2"><br><strong>Scores</strong></td></tr>
                <tr><td>HR Round</td><td>{{ hr_score }}</td></tr>
                <tr><td>Technical Round</td><td>{{ tech_score }}</td></tr>
                <tr><td>Final Round</td><td>{{ final_score }}</td></tr>

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
            "manager_name": manager.name,
            "hr_name": hr.name,

            "candidate_name": candidate.candidate_name,
            "designation": designation.name,
            "department": department.name,

            "experience": candidate.experience_years,
            "qualification": data.get("qualification"),
            "last_organization": data.get("last_organization"),

            "hr_interviewer": data.get("hr_interviewer"),
            "tech_interviewer": data.get("tech_interviewer"),
            "final_interviewer": data.get("final_interviewer"),

            "hr_score": data.get("hr_score"),
            "tech_score": data.get("tech_score"),
            "final_score": data.get("final_score"),

            "current_ctc": data.get("current_ctc"),
            "expected_ctc": data.get("expected_ctc"),
            "offered_ctc": data.get("offered_ctc"),

            "notice_period": data.get("notice_period"),
            "office_location": candidate.job.mrf.location,

            "source": candidate.source,
            "mrf": mrf.mrf_name,
            "hiring_type": data.get("hiring_type"),

            "remarks": data.get("remarks"),
        }

        # --- Render email ---
        template = Template(html_content)
        html_rendered = template.render(Context(context))

        # --- Trigger workflow ---
        automation_engine(candidate, candidate.status, "approval_pending")

        # --- Send email ---
        send_email(
            subject="Approval Required – Candidate Hiring",
            text="Approval required. Please view this email in HTML format.",
            to=manager.email,
            template=html_rendered
        )

        return Response(
            {"status": "Approval note sent successfully"},
            status=status.HTTP_200_OK
        )

def aggregate_interview_feedback(job_application):
    feedbacks = job_application.interview_feedbacks.all()

    result = {
        # Interviewers
        "hr_interviewer": None,
        "tech_interviewer": None,
        "final_interviewer": None,

        # Scores
        "hr_score": None,
        "tech_score": None,
        "final_score": None,

        # Common fields
        "qualification": None,
        "last_organization": None,
        "notice_period": None,
        "current_ctc": None,
        "expected_ctc": None,
        "remarks": None,
    }

    for fb in feedbacks:
        # ---- Interviewer names ----
        if fb.interview_round == "hr_round":
            result["hr_interviewer"] = fb.interviewer_name
            result["hr_score"] = fb.get_round_avg()

        elif fb.interview_round == "technical_round":
            result["tech_interviewer"] = fb.interviewer_name
            result["tech_score"] = fb.get_round_avg()

        elif fb.interview_round == "final_round":
            result["final_interviewer"] = fb.interviewer_name
            result["final_score"] = fb.get_round_avg()

        # ---- Common fields (pick first non-null) ----
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

        feedback_data = aggregate_interview_feedback(candidate)

        response = {
            "candidate_id": str(candidate.id),
            "candidate_name": candidate.candidate_name,

            "designation": candidate.job.mrf.designation.name,
            "department": candidate.job.mrf.department.name,

            **feedback_data
        }

        return Response(response, status=status.HTTP_200_OK)
