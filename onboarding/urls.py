from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import UploadJobApplicationDocumentAPI,UpdatestatusAPI,SendApprovalNoteAPIView,CandidateInterviewSummaryAPIView,SalaryAnnexureHistoryViewSet,SalaryAnnexureViewSet,ReviewJobApplicationDocumentsAPI,SendForOfferLetterEmailAPI,SendForSalaryAnnexureEmailAPI
from .utils.opensign import opensign_webhook
from .utils.zoho_sign import zoho_sign_webhook
from .views import send_offer_letter_view, bulk_send_offers, docusign_webhook
# router = DefaultRouter()
# router.register(r"salary-annexures", SalaryAnnexureViewSet, basename="salary-annexure")
# router.register(r"salary-annexure-history", SalaryAnnexureHistoryViewSet, basename="salary-annexure-history")

urlpatterns = [
    path("application/<str:id>/update-status/",UpdatestatusAPI.as_view(),name="update-application-status"),
    # path('create-candidate/', CreateCandidateAPIView.as_view(), name='create-candidate'),
    # path('create-job/', JobCreateAPIView.as_view(), name='create-job'),
    path('application/<str:id>/documents/upload/',UploadJobApplicationDocumentAPI.as_view(),name='upload-documents'),
    path('application/<str:id>/documents/review/',ReviewJobApplicationDocumentsAPI.as_view(),name='review-documents'),
    path("send-approval-note/", SendApprovalNoteAPIView.as_view(),name="send-approval-note"),
    path("candidates/<uuid:candidate_id>/interview-summary/",CandidateInterviewSummaryAPIView.as_view(),name="candidate-interview-summary"),
    # path('opensign/webhook/',opensign_webhook,name="opensign-webhook"),
    path('zohosign/webhook/',zoho_sign_webhook,name="zohosign-webhook"),
    path('send-for-offer-letter/<str:id>/',SendForOfferLetterEmailAPI.as_view(),name='send-for-offer-letter'),
    path('send-for-salary-annexure/<str:id>/',SendForSalaryAnnexureEmailAPI.as_view(),name='send-for-salary-annexure'),
    # path("", include(router.urls)),
    path("send-offer/<uuid:application_id>/", send_offer_letter_view),
    path("bulk-send-offers/", bulk_send_offers),
    path("docusign/webhook/", docusign_webhook)
]
