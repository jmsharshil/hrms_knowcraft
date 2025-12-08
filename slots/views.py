# slots/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from .graph import get_interviewer_busy_slots
from .availability import generate_free_slots_for_day
from .serializers import FreeSlotSerializer,InterviewerCreateSerializer
from slots.models import Interviewer
from rest_framework import permissions

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
                    "start": b["start"],
                    "end": b["end"],
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
