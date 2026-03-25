# booking/serializers.py
from rest_framework import serializers
from .models import Booking
from slots.models import Interviewer

class BookingSerializer(serializers.ModelSerializer):
    attendees = serializers.PrimaryKeyRelatedField(
        queryset=Interviewer.objects.all(), required=False, allow_null=True, many=True
    )
    class Meta:
        model = Booking
        fields = ["id", "candidate", "interviewer", "meeting_id", "meeting_link", "start", "end", "created_at","attendees"]
        read_only_fields = ["meeting_id", "meeting_link", "created_at"]
