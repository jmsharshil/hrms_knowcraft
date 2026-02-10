from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import UploadJobApplicationDocumentAPI,UpdatestatusAPI,SendApprovalNoteAPIView,CandidateInterviewSummaryAPIView,SalaryAnnexureHistoryViewSet,SalaryAnnexureViewSet
from .utils.opensign import opensign_webhook

router = DefaultRouter()
router.register(r"salary-annexures", SalaryAnnexureViewSet, basename="salary-annexure")
router.register(r"salary-annexure-history", SalaryAnnexureHistoryViewSet, basename="salary-annexure-history")

urlpatterns = [
    path("application/<str:id>/update-status/",UpdatestatusAPI.as_view(),name="update-application-status"),
    # path('create-candidate/', CreateCandidateAPIView.as_view(), name='create-candidate'),
    # path('create-job/', JobCreateAPIView.as_view(), name='create-job'),
    path('application/<str:id>/documents/upload/',UploadJobApplicationDocumentAPI.as_view(),name='upload-documents'),
    path("send-approval-note/", SendApprovalNoteAPIView.as_view(),name="send-approval-note"),
    path("candidates/<uuid:candidate_id>/interview-summary/",CandidateInterviewSummaryAPIView.as_view(),name="candidate-interview-summary"),
    path('opensign/webhook/',opensign_webhook,name="opensign-webhook"),
    path("", include(router.urls)),
]
