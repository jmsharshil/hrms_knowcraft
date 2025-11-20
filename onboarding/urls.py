from django.urls import path
from .views import UpdateStageAPI,CreateCandidateAPIView,UploadCandidateDocumentAPI,JobCreateAPIView
from .utils.opensign import opensign_webhook
urlpatterns = [
    path("candidate/<int:candidate_id>/update-stage/",UpdateStageAPI.as_view(),name="update-stage"),
    path('create-candidate/', CreateCandidateAPIView.as_view(), name='create-candidate'),
    path('create-job/', JobCreateAPIView.as_view(), name='create-job'),
    path('candidates/<int:candidate_id>/documents/upload/',UploadCandidateDocumentAPI.as_view(),name='upload-documents'),
    path('opensign/webhook/',opensign_webhook,name="opensign-webhook")
]
