# booking/serializers.py
from rest_framework import serializers
from .models import Candidate, Booking

class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ["id", "full_name", "email"]

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "candidate", "interviewer", "meeting_id", "meeting_link", "start", "end", "created_at"]
        read_only_fields = ["meeting_id", "meeting_link", "created_at"]
