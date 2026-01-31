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
from onboarding.utils.engine import automation_engine
from jobs.models import JobApplication

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
        try:
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
        except Exception as e:
            print(f"Can Not get the Slots:{e}")
            return Response({
                "error":"Unable to get slots! Interviewer is not a part of the organisation."
            },status=status.HTTP_404_NOT_FOUND)
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
        application_id = request.data.get('job_application')
        application = get_object_or_404(JobApplication, id=application_id)

        # Determine new status based on current application status
        current_status = application.status
        new_status = self._get_status_after_interview(application,current_status, request.data.get('is_selected', 'hire'))
        automation_engine(application, application.status, new_status)

        # Save feedback
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

    def _get_status_after_interview(self,application, current_status, is_selected):
        """
        Determine next status of JobApplication based on current_status and is_selected
        """
        application_status_mapping = {
            'interview_pending_1': 'interview_done_1',
            'interview_pending_2': 'interview_done_2',
            'interview_pending_3': 'interview_done_3',
            'interview_pending_final': 'interview_done_final',
            'interview_pending_management_client': 'interview_done_management_client',
        }

        # Default: move to "done" stage
        new_status = application_status_mapping.get(current_status, current_status)

        # If candidate is selected, move to next round or selected
        automation_engine(application,application.status,new_status)
        if is_selected in ['hire', 'strong_hire']:
            if new_status == 'interview_done_1':
                if application.job.mrf.interviewer_email_2:
                    new_status = 'interview_next_2'
                elif application.job.mrf.interviewer_email_3:
                    new_status = 'interview_next_3'
                elif application.job.mrf.interviewer_email_final:
                    new_status = 'interview_next_final'
                elif application.job.mrf.interviewer_email_management_client:
                    new_status = 'interview_next_management_client'
                else:
                    new_status = 'selected'
            elif new_status == 'interview_done_2':
                if application.job.mrf.interviewer_email_3:
                    new_status = 'interview_next_3'
                elif application.job.mrf.interviewer_email_final:
                    new_status = 'interview_next_final'
                elif application.job.mrf.interviewer_email_management_client:
                    new_status = 'interview_next_management_client'
                else:
                    new_status = 'selected'
            elif new_status == 'interview_done_3':
                if application.job.mrf.interviewer_email_final:
                    new_status = 'interview_next_final'
                elif application.job.mrf.interviewer_email_management_client:
                    new_status = 'interview_next_management_client'
                else:
                    new_status = 'selected'
            elif new_status == 'interview_done_final':
                if application.job.mrf.interviewer_email_management_client:
                    new_status = 'interview_next_management_client'
                else:
                    new_status = 'selected'
            elif new_status == 'interview_done_management_client':
                    new_status = 'selected'
        else:
            # If not selected, move to rejected
            reject_mapping = {
                'interview_done_1': 'interview_rejected_1',
                'interview_done_2': 'interview_rejected_2',
                'interview_done_3': 'interview_rejected_3',
                'interview_done_final': 'interview_rejected_final',
                'interview_done_management_client': 'interview_rejected_management_client',
            }
            new_status = reject_mapping.get(new_status, new_status)

        return new_status

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
        serializer = InterviewFeedbackUpdateSerializer(feedback, data=request.data)
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
        application = feedback.job_application

        # Update status if is_selected is being updated
        is_selected = request.data.get('is_selected', None)
        if is_selected is not None:
            new_status = self._get_status_after_patch(application, is_selected)
            if new_status:
                automation_engine(application, application.status, new_status)

        serializer = InterviewFeedbackUpdateSerializer(feedback, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Interview feedback partially updated successfully",
                "data": InterviewFeedbackDetailSerializer(feedback).data
            },
            status=status.HTTP_200_OK
        )

    def _get_status_after_patch(self, application, is_selected):
        """
        Determine new status for partial update (PATCH)
        """
        current_status = application.status

        # Selected
        if is_selected in ['hire', 'strong_hire']:
            if current_status in ['interview_done_1', 'interview_rejected_1']:
                if application.job.mrf.interviewer_email_2:
                    return 'interview_next_2'
                elif application.job.mrf.interviewer_email_3:
                    return 'interview_next_3'
                elif application.job.mrf.interviewer_email_final:
                    return 'interview_next_final'
                elif application.job.mrf.interviewer_email_management_client:
                    return 'interview_next_management_client'
                else:
                    return 'selected'
            elif current_status in ['interview_done_2', 'interview_rejected_2']:
                if application.job.mrf.interviewer_email_3:
                    return 'interview_next_3'
                elif application.job.mrf.interviewer_email_final:
                    return 'interview_next_final'
                elif application.job.mrf.interviewer_email_management_client:
                    return 'interview_next_management_client'
                else:
                    return 'selected'
            elif current_status in ['interview_done_3', 'interview_rejected_3']:
                if application.job.mrf.interviewer_email_final:
                    return 'interview_next_final'
                elif application.job.mrf.interviewer_email_management_client:
                    return 'interview_next_management_client'
                else:
                    return 'selected'
            elif current_status in ['interview_done_final', 'interview_rejected_final']:
                if application.job.mrf.interviewer_email_management_client:
                    return 'interview_next_management_client'
                else:
                    return 'selected'
            elif current_status in ['interview_done_management_client', 'interview_rejected_management_client']:
                return 'selected'
        else:
            # Not selected
            mapping = {
                'interview_done_1': 'interview_rejected_1',
                'interview_done_2': 'interview_rejected_2',
                'interview_done_3': 'interview_rejected_3',
                'interview_done_final': 'interview_rejected_final',
                'interview_done_management_client': 'interview_rejected_management_client',
                'interview_next_2': 'interview_rejected_1',
                'interview_next_3': 'interview_rejected_2',
                'interview_next_final': 'interview_rejected_3',
                'interview_next_management_client': 'interview_rejected_final',
                'selected': 'interview_rejected_final',
            }
            return mapping.get(current_status, current_status)