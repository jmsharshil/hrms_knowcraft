from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import (
    UploadJobApplicationDocumentAPI, UpdatestatusAPI, SendApprovalNoteAPIView,
    CandidateInterviewSummaryAPIView, SalaryAnnexureHistoryViewSet, SalaryAnnexureViewSet,
    ReviewJobApplicationDocumentsAPI, SendForOfferLetterEmailAPI, SendForSalaryAnnexureEmailAPI,
    DownloadJobApplicationDocumentsView, DownloadApprovalNoteAPIView, RevertOfferAPIView,
    EmailLogViewSet,
    ResolveEscalationAPI, AssignBuddyAPI, CompleteSurveyAPI, ScheduleD45CallAPI, ScheduleD90CallAPI,
    SearchTeamsUsersAPI, InitiateOnboardingAPI, RevertRejectionAPI, GetSurveyStructureAPI
)
from .utils.opensign import opensign_webhook
from .utils.zoho_sign import zoho_sign_webhook
from .views import send_offer_letter_view, bulk_send_offers, docusign_webhook

router = DefaultRouter()
# router.register(r"salary-annexures", SalaryAnnexureViewSet, basename="salary-annexure")
# router.register(r"salary-annexure-history", SalaryAnnexureHistoryViewSet, basename="salary-annexure-history")
router.register(r"email-logs", EmailLogViewSet, basename="email-logs")

urlpatterns = [
    path("application/<str:id>/update-status/",UpdatestatusAPI.as_view(),name="update-application-status"),
    path("application/<str:id>/revert-rejection/",RevertRejectionAPI.as_view(),name="revert-rejection-status"),
    # path('create-candidate/', CreateCandidateAPIView.as_view(), name='create-candidate'),
    # path('create-job/', JobCreateAPIView.as_view(), name='create-job'),
    path('application/<str:id>/documents/upload/',UploadJobApplicationDocumentAPI.as_view(),name='upload-documents'),
    path('application/<str:id>/documents/review/',ReviewJobApplicationDocumentsAPI.as_view(),name='review-documents'),
    path("application/<str:id>/documents/download/",DownloadJobApplicationDocumentsView.as_view(),name="download-documents"),
    path("approval-note/<str:id>/download/", DownloadApprovalNoteAPIView.as_view(), name="download-approval-note"),
    path("send-approval-note/", SendApprovalNoteAPIView.as_view(),name="send-approval-note"),
    path("candidates/<uuid:candidate_id>/interview-summary/",CandidateInterviewSummaryAPIView.as_view(),name="candidate-interview-summary"),
    # path('opensign/webhook/',opensign_webhook,name="opensign-webhook"),
    path('zohosign/webhook/',zoho_sign_webhook,name="zohosign-webhook"),
    path('send-for-offer-letter/<str:id>/',SendForOfferLetterEmailAPI.as_view(),name='send-for-offer-letter'),
    path('application/<str:id>/offer/revert/',RevertOfferAPIView.as_view(),name='revert-offer'),
    path('send-for-salary-annexure/<str:id>/',SendForSalaryAnnexureEmailAPI.as_view(),name='send-for-salary-annexure'),
    path('application/<str:id>/initiate-onboarding/', InitiateOnboardingAPI.as_view(), name='initiate-onboarding'),
    path('application/<str:id>/resolve-escalation/', ResolveEscalationAPI.as_view(), name='resolve-escalation'),
    path('application/<str:id>/assign-buddy/', AssignBuddyAPI.as_view(), name='assign-buddy'),
    path('application/<str:id>/survey-completed/', CompleteSurveyAPI.as_view(), name='survey-completed'),
    path('application/<str:id>/survey-structure/', GetSurveyStructureAPI.as_view(), name='survey-structure'),
    path('application/<str:id>/d45-scheduled/', ScheduleD45CallAPI.as_view(), name='d45-scheduled'),
    path('application/<str:id>/d90-scheduled/', ScheduleD90CallAPI.as_view(), name='d90-scheduled'),
    path('teams/users/search/', SearchTeamsUsersAPI.as_view(), name='search-teams-users'),
    path("", include(router.urls)),
    # path("send-offer/<uuid:application_id>/", send_offer_letter_view),
    # path("bulk-send-offers/", bulk_send_offers),
    # path("docusign/webhook/", docusign_webhook)
]
