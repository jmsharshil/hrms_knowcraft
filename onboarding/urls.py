from django.urls import path
from .views import UploadJobApplicationDocumentAPI,UpdatestatusAPI
from .utils.opensign import opensign_webhook
urlpatterns = [
    path("application/<str:id>/update-status/",UpdatestatusAPI.as_view(),name="update-application-status"),
    # path('create-candidate/', CreateCandidateAPIView.as_view(), name='create-candidate'),
    # path('create-job/', JobCreateAPIView.as_view(), name='create-job'),
    path('application/<str:id>/documents/upload/',UploadJobApplicationDocumentAPI.as_view(),name='upload-documents'),
    path('opensign/webhook/',opensign_webhook,name="opensign-webhook")
]
