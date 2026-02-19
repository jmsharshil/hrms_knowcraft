from django.urls import path
from .views import AvailableSlotsForInterviewerView,InterviewerListView
from slots.views import InterviewerView,InterviewFeedbackListCreateAPIView,InterviewFeedbackDetailAPIView
urlpatterns = [
    path("available/", AvailableSlotsForInterviewerView.as_view()),
    path("interviewer/add/", InterviewerView.as_view()),
    path("interviewer/list/", InterviewerListView.as_view()),
    path("interviewer/<str:pk>/", InterviewerView.as_view()),
    path("interview-feedback/",InterviewFeedbackListCreateAPIView.as_view(),name="interview-feedback-list-create"),
    path("interview-feedback/<uuid:pk>/",InterviewFeedbackDetailAPIView.as_view(),name="interview-feedback-detail"),
]
