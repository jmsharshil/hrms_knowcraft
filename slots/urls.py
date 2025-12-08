from django.urls import path
from .views import AvailableSlotsForInterviewerView
from slots.views import InterviewerCreateView
urlpatterns = [
    path("available/", AvailableSlotsForInterviewerView.as_view()),
    path("interviewer/add/", InterviewerCreateView.as_view()),
    
]
