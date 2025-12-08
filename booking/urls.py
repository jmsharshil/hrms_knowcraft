from django.urls import path
from .views import CandidateBookSlotView,SendSlotSelectionEmailView,FetchMeetingData,MeetingWebhookView

urlpatterns = [
    path("send-email/", SendSlotSelectionEmailView.as_view()),
    path("candidate/<uuid:candidate_id>/book/", CandidateBookSlotView.as_view()),
    path("fetch-data/", FetchMeetingData.as_view()),
    path("meeting-webhook/", MeetingWebhookView.as_view()),
]
