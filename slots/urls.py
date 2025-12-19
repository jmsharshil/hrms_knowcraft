from django.urls import path
from .views import AvailableSlotsForInterviewerView
from slots.views import InterviewerCreateView,InterviewFeedbackListCreateAPIView,InterviewFeedbackDetailAPIView
urlpatterns = [
    path("available/", AvailableSlotsForInterviewerView.as_view()),
    path("interviewer/add/", InterviewerCreateView.as_view()),
    path("interview-feedback/",InterviewFeedbackListCreateAPIView.as_view(),name="interview-feedback-list-create"),
    path("interview-feedback/<uuid:pk>/",InterviewFeedbackDetailAPIView.as_view(),name="interview-feedback-detail"),
]
