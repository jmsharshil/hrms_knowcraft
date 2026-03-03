from django.urls import path
from .views import CandidateBookSlotView,SendSlotSelectionEmailView,FetchMeetingData,MeetingWebhookView,CandidateBookInPersonInterviewView,BranchWiseInterviewReportView

urlpatterns = [
    path("send-email/", SendSlotSelectionEmailView.as_view()),
    path("candidate/<uuid:candidate_id>/book/", CandidateBookSlotView.as_view()),
    path("candidate/book/inperson/", CandidateBookInPersonInterviewView.as_view()),
    path("interviews/report/",BranchWiseInterviewReportView.as_view()),
    path("fetch-data/", FetchMeetingData.as_view()),
    path("meeting-webhook/", MeetingWebhookView.as_view()),
]
