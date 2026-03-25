from django.urls import path
from .views import CandidateBookSlotView,SendSlotSelectionEmailView,FetchMeetingData,MeetingWebhookView,CandidateBookInPersonInterviewView,BranchWiseInterviewReportView
from .views import GraphWebhookView,RescheduleBookingView,CancelBookingView,UpdateAttendeesView
urlpatterns = [
    path("send-email/", SendSlotSelectionEmailView.as_view()),
    path("candidate/<uuid:candidate_id>/book/", CandidateBookSlotView.as_view()),
    path("candidate/book/inperson/", CandidateBookInPersonInterviewView.as_view()),
    path("interviews/report/",BranchWiseInterviewReportView.as_view()),
    path("fetch-data/", FetchMeetingData.as_view()),
    path("meeting-webhook/", MeetingWebhookView.as_view()),
    path("webhooks/graph/", GraphWebhookView.as_view()),
    path("<uuid:candidate_id>/reschedule/", RescheduleBookingView.as_view()),
    path("<uuid:candidate_id>/cancel/", CancelBookingView.as_view()),
    path("<uuid:candidate_id>/update-attendees/", UpdateAttendeesView.as_view())
]
