# slots/serializers.py
from rest_framework import serializers
from .models import Interviewer

class FreeSlotSerializer(serializers.Serializer):
    slot_id = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

class InterviewerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interviewer
        fields = ["id", "name", "email"]
