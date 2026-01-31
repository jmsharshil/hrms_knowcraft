# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from django.shortcuts import get_object_or_404
from .models import JobApplicationDocument
from onboarding.utils.engine import automation_engine
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