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
from .serializers import CandidateBGVSerializer, CandidateBGVListSerializer
from .services import (
    initiate_bgv,
    onboard_individual,
    trigger_verifications,
    get_individual_status,
    get_verification_report,
)


logger = logging.getLogger(__name__)


class CandidateBGVViewSet(viewsets.ModelViewSet):
    """
    CRUD + custom actions for Background Verification records.
    """

    queryset = CandidateBGV.objects.select_related("candidate").all()

    def get_serializer_class(self):
        if self.action == 'list':
            return CandidateBGVListSerializer
        return CandidateBGVSerializer

    @action(detail=True, methods=["post"])
    def reinitiate(self, request, pk=None):
        """
        Re-initiate BGV for an existing record.
        Uses update_or_create inside initiate_bgv, so no
        OneToOneField violation.
        """
        bgv = self.get_object()
        extra_data = request.data.get("extra_data", {})
        result = initiate_bgv(bgv.candidate, extra_data=extra_data or None)
        serializer = self.get_serializer(result)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="initiate-by-application")
    def initiate_by_application(self, request):
        """
        Initiate BGV (onboard + start verifications) by providing a job application ID.

        POST {
            "application_id": "<uuid>",
            "extra_data": {                       # optional
                "fathersName": "...",
                "gender": "M",                    # M, F, T, O, U
                "dob": "DD/MM/YYYY",
                "city": "...",
                "permanentAddress": {
                    "line1": "...",
                    "line2": "...",
                    "city": "...",
                    "state": "...",
                    "pincode": "...",
                    "country": "IN",
                    "fullAddress": "..."
                },
                "currentAddress": "full address string",
                "verifications": [{"code": "CCRV"}, {"code": "PANV"}]
            }
        }
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
        
        if not hasattr(application,"documents"):
            return Response("No documents found for given application.")
        
        extra_data = request.data.get("extra_data", {})
        result = initiate_bgv(application, extra_data=extra_data or None)
        serializer = self.get_serializer(result)

        http_status = (
            status.HTTP_200_OK
            if result.status == "initiated"
            else status.HTTP_502_BAD_GATEWAY
        )
        return Response(serializer.data, status=http_status)

    @action(detail=False, methods=["post"], url_path="onboard-only")
    def onboard_only(self, request):
        """
        Step 1: Onboard an individual into OnGrid WITHOUT starting verifications.
        Use this when you need to register the candidate first and initiate
        verifications later (e.g., after collecting father's name / address).

        POST {
            "application_id": "<uuid>",
            "extra_data": { ... }                 # optional
        }
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

        extra_data = request.data.get("extra_data", {})
        result = onboard_individual(application, extra_data=extra_data or None)

        if result is None:
            return Response(
                {"error": "Failed to onboard individual on OnGrid."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        serializer = self.get_serializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="trigger-verifications")
    def trigger_verifications_action(self, request, pk=None):
        """
        Step 2: Trigger verifications for an already-onboarded individual.

        POST {
            "verification_codes": ["CCRV", "PANV"]   # optional, defaults to CCRV
        }
        """
        bgv = self.get_object()

        if not bgv.ongrid_individual_id:
            return Response(
                {"error": "Individual not yet onboarded on OnGrid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        codes = request.data.get("verification_codes", None)
        data, success = trigger_verifications(bgv.ongrid_individual_id, codes)

        if success:
            bgv.refresh_from_db()
            serializer = self.get_serializer(bgv)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"error": "Failed to trigger verifications.", "details": data},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    @action(detail=True, methods=["get"], url_path="ongrid-status")
    def ongrid_status(self, request, pk=None):
        """
        Fetch current individual status from OnGrid API (polling).
        Persists the response into CandidateBGV.ongrid_status and updates
        report_url / status so the get-by-id endpoint reflects the latest state.
        """
        bgv = self.get_object()

        if not bgv.ongrid_individual_id:
            return Response(
                {"error": "No OnGrid individual ID found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Pass bgv so the status payload is saved to the DB record
        data = get_individual_status(bgv.ongrid_individual_id, bgv_instance=bgv)
        if data is None:
            return Response(
                {"error": "Failed to fetch status from OnGrid."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="verification-report")
    def verification_report(self, request, pk=None):
        """
        Fetch verification report/results from OnGrid API.
        """
        bgv = self.get_object()

        if not bgv.ongrid_individual_id:
            return Response(
                {"error": "No OnGrid individual ID found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = get_verification_report(bgv.ongrid_individual_id)
        if data is None:
            return Response(
                {"error": "Failed to fetch report from OnGrid."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="send-for-bgv")
    def send_for_bgv(self, request, pk=None):
        candidate = JobApplication.objects.get(id=pk)
        if candidate:
            from utils import send_notification_for_bgv
            send_notification_for_bgv(candidate)
            return Response({"message": "Notification sent successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Candidate not found."}, status=status.HTTP_404_NOT_FOUND)
