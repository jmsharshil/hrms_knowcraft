# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from django.shortcuts import get_object_or_404
from .models import Candidate,CandidateDocument
from onboarding.utils.engine import automation_engine
from .serializers import CandidateDocumentSerializer,JobCreateSerializer,CandidateSerializer
import logging

logger = logging.getLogger("workflow")


class UpdateStageAPI(APIView):
    permission_classes = [permissions.AllowAny] 
    def post(self, request, candidate_id):

        new_stage = request.data.get("stage") or request.POST.get("stage")

        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response({"error": "Candidate not found"}, status=404)

        old_stage = candidate.stage
        # candidate.stage = new_stage
        # candidate.save()

        logger.info(f"[STAGE] {candidate.name}: {old_stage} → {new_stage}")

        ok,reason = automation_engine(candidate, old_stage, new_stage)
        if ok:
            return Response({"success": ok,"stage":candidate.stage})
        else:
            return Response({"Error:",reason})

class JobCreateAPIView(APIView):
    permission_classes = [permissions.AllowAny] 
    def post(self, request):
        serializer = JobCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            job = serializer.save()
            return Response({
                "status": True,
                "message": "Job created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
class CreateCandidateAPIView(APIView):
    permission_classes = [permissions.AllowAny] 
    def post(self, request):
        serializer = CandidateSerializer(data=request.data)
        if serializer.is_valid():
            candidate = serializer.save()
            return Response({
                "success": True,
                "message": "Candidate created successfully",
                "data": CandidateSerializer(candidate).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    

class UploadCandidateDocumentAPI(APIView):
    permission_classes = [permissions.AllowAny]  # if public for candidate
    
    def post(self, request, candidate_id):
        candidate = get_object_or_404(Candidate, id=candidate_id)

        files = request.FILES.getlist("files")
        doc_type = request.data.get("doc_type", None)

        if not files:
            return Response({"error": "No file uploaded"}, status=400)

        saved_docs = []

        for f in files:
            doc = CandidateDocument.objects.create(
                candidate=candidate,
                file=f,
                doc_type=doc_type
            )
            saved_docs.append(CandidateDocumentSerializer(doc).data)

        # OPTIONAL: When first doc uploaded → move to docs_received
        if candidate.stage == "docs_pending":
            ok, reason = automation_engine(candidate, "docs_pending", "docs_uploaded")
            if not ok:
                return Response({"error": reason}, status=400)
        elif candidate.stage == "salary_docs_pending":
            ok, reason = automation_engine(candidate, "salary_docs_pending", "salary_docs_uploaded")
            if not ok:
                return Response({"error": reason}, status=400)
        elif candidate.stage == "resignation_pending":
            ok, reason = automation_engine(candidate, "resignation_pending", "resignation_uploaded")
            if not ok:
                return Response({"error": reason}, status=400)

        return Response({
            "message": "Documents uploaded successfully.",
            "documents": saved_docs
        }, status=201)