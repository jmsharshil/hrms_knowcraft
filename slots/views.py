# slots/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from .graph import get_interviewer_busy_slots
from .availability import generate_free_slots_for_day
from .serializers import FreeSlotSerializer,InterviewerCreateSerializer,InterviewFeedbackCreateSerializer,InterviewFeedbackUpdateSerializer,InterviewFeedbackDetailSerializer,InterviewFeedbackListSerializer
from slots.models import Interviewer,InterviewFeedback
from rest_framework import permissions
from rest_framework import status
from django.shortcuts import get_object_or_404

IST = ZoneInfo("Asia/Kolkata")


class AvailableSlotsForInterviewerView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        candidate_id = request.query_params.get("candidate_id")
        interviewer_id = request.query_params.get("interviewer_id")
        days = int(request.query_params.get("days", 7))

        if not candidate_id or not interviewer_id:
            return Response({"detail": "candidate_id and interviewer_id are required"}, status=400)

        interviewer = Interviewer.objects.filter(id=interviewer_id).first()
        if not interviewer:
            return Response({"detail": "Interviewer not found"}, status=404)

        today_ist = datetime.now(IST).date()

        all_free = []
        all_busy = []

        for offset in range(days):
            d = today_ist + timedelta(days=offset)
            if d.weekday() >= 5:
                continue

            day_start = datetime.combine(d, datetime.min.time(), IST)
            day_end = datetime.combine(d, datetime.max.time(), IST)

            daily_busy = get_interviewer_busy_slots(interviewer.email, day_start, day_end)
            all_busy.extend(daily_busy)

            free_today = generate_free_slots_for_day(daily_busy, d, interviewer)
            all_free.extend(free_today)

        return Response({
            "free_slots": FreeSlotSerializer(all_free, many=True).data,
            "busy_slots": [
                {
                    "start": b["start"].strftime("%Y-%m-%d %H:%M:%S"),   # -> 2025-12-11T14:30:00+05:30
                    "end": b["end"].strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": b["reason"]
                }
                for b in all_busy
            ]
        })



class InterviewerCreateView(APIView):
    def post(self, request):
        serializer = InterviewerCreateSerializer(data=request.data)
        if serializer.is_valid():
            interviewer = serializer.save()
            return Response({
                "message": "Interviewer added successfully",
                "interviewer": serializer.data
            }, status=201)
        return Response(serializer.errors, status=400)

class InterviewFeedbackListCreateAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        List all feedbacks
        Optional filters:
        - ?job_application=<uuid>
        - ?interview_round=round_1
        """
        queryset = InterviewFeedback.objects.select_related(
            "job_application", "job_application__job"
        ).all()

        job_application = request.query_params.get("job_application")
        interview_round = request.query_params.get("interview_round")

        if job_application:
            queryset = queryset.filter(job_application_id=job_application)

        if interview_round:
            queryset = queryset.filter(interview_round=interview_round)

        queryset = queryset.order_by("-created_at")

        serializer = InterviewFeedbackListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create interview feedback
        """
        if request.data.get('is_selected'):
            from onboarding.utils.engine import automation_engine
            from jobs.models import JobApplication
            application_id = request.data.get('job_application')
            application = JobApplication.objects.filter(id=application_id).first()
            new_status = None
            if application.status == 'interview_pending_1':
                new_status = 'interview_done_1'
            elif application.status == 'interview_pending_2':
                new_status = 'interview_done_2'
            elif application.status == 'interview_pending_3':
                new_status = 'interview_done_3'
            elif application.status == 'interview_pending_final':
                new_status = 'interview_done_final'
            automation_engine(application,application.status,new_status)
        serializer = InterviewFeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feedback = serializer.save()

        return Response(
            {
                "message": "Interview feedback saved successfully",
                "data": InterviewFeedbackDetailSerializer(feedback).data
            },
            status=status.HTTP_201_CREATED
        )

class InterviewFeedbackDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, pk):
        return get_object_or_404(
            InterviewFeedback.objects.select_related(
                "job_application", "job_application__job"
            ),
            pk=pk
        )

    def get(self, request, pk):
        """
        Get feedback by ID
        """
        feedback = self.get_object(pk)
        serializer = InterviewFeedbackDetailSerializer(feedback)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """
        Full update feedback
        """
        feedback = self.get_object(pk)
        serializer = InterviewFeedbackUpdateSerializer(
            feedback, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Interview feedback updated successfully",
                "data": InterviewFeedbackDetailSerializer(feedback).data
            },
            status=status.HTTP_200_OK
        )

    def patch(self, request, pk):
        """
        Partial update feedback
        """
        feedback = self.get_object(pk)
        serializer = InterviewFeedbackUpdateSerializer(
            feedback, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Interview feedback partially updated successfully",
                "data": InterviewFeedbackDetailSerializer(feedback).data
            },
            status=status.HTTP_200_OK
        )
