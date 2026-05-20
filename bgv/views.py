# bgv/views.py

import logging

from django.conf import settings
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from jobs.models import JobApplication

from .models import CandidateBGV
from .serializers import CandidateBGVSerializer
from .services import initiate_bgv


logger = logging.getLogger(__name__)


class CandidateBGVViewSet(viewsets.ModelViewSet):
    """
    CRUD + custom actions for Background Verification records.
    """

    queryset = CandidateBGV.objects.select_related("candidate").all()
    serializer_class = CandidateBGVSerializer

    @action(detail=True, methods=["post"])
    def reinitiate(self, request, pk=None):
        """
        Re-initiate BGV for an existing record.
        Uses update_or_create inside initiate_bgv, so no
        OneToOneField violation.
        """
        bgv = self.get_object()
        result = initiate_bgv(bgv.candidate)
        serializer = self.get_serializer(result)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="initiate-by-application")
    def initiate_by_application(self, request):
        """
        Manually initiate BGV by providing a job application ID.
        POST {"application_id": "<uuid>"}
        """
        application_id = request.data.get("application_id")
        if not application_id:
            return Response(
                {"error": "application_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application = JobApplication.objects.get(id=application_id)
        except JobApplication.DoesNotExist:
            return Response(
                {"error": "Job application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = initiate_bgv(application)
        serializer = self.get_serializer(result)

        http_status = (
            status.HTTP_200_OK
            if result.status == "initiated"
            else status.HTTP_502_BAD_GATEWAY
        )
        return Response(serializer.data, status=http_status)


class OnGridWebhookAPIView(APIView):
    """
    Receives webhook callbacks from OnGrid.
    No auth required (public endpoint), but verified via shared secret header.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.data

        # ── secret verification ──────────────────────────────
        secret = request.headers.get("X-ONGRID-SECRET", "")
        expected = getattr(settings, "ONGRID_WEBHOOK_SECRET", "")

        if not expected or secret != expected:
            logger.warning("OnGrid webhook: invalid secret header.")
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ── extract fields ───────────────────────────────────
        individual_id = payload.get("individualId")
        activity_type = payload.get("activityType")

        if not individual_id:
            return Response(
                {"error": "individualId is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            bgv = CandidateBGV.objects.get(
                ongrid_individual_id=individual_id,
            )
        except CandidateBGV.DoesNotExist:
            logger.warning(
                "OnGrid webhook: no BGV found for individualId=%s",
                individual_id,
            )
            return Response(
                {"error": "BGV record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── update record ────────────────────────────────────
        bgv.callback_payload = payload

        if activity_type == "VerificationsConcluded":
            bgv.status = "completed"
            bgv.completed_at = timezone.now()
            report_url = payload.get("reportDownloadUrl")
            if report_url:
                bgv.report_url = report_url

        elif activity_type == "DataInsufficient":
            bgv.status = "insufficient"

        else:
            bgv.status = "in_progress"

        bgv.save()

        logger.info(
            "OnGrid webhook processed: individual=%s, activity=%s, status=%s",
            individual_id,
            activity_type,
            bgv.status,
        )

        return Response(
            {"success": True},
            status=status.HTTP_200_OK,
        )