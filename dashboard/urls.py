from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardAPIView,
    RecruitmentCostViewSet,
    CandidateExperienceFeedbackSubmitView,
)

router = DefaultRouter()
router.register(r'recruitment-costs', RecruitmentCostViewSet, basename='recruitment-cost')

urlpatterns = [
    # Single dashboard endpoint returning all 10 metrics
    path('', DashboardAPIView.as_view(), name='dashboard'),

    # Public candidate feedback submission
    path('feedback/submit/', CandidateExperienceFeedbackSubmitView.as_view(), name='feedback-submit'),

    # CRUD for recruitment costs
    path('', include(router.urls)),
]

# ============================================
# Available Dashboard Endpoints
# ============================================
#
# GET    /api/dashboard/                          - All 10 metrics in one response
#        ?job_id=<uuid>                           - Filter by job
#        ?department_id=<uuid>                    - Filter by department
#        ?date_from=YYYY-MM-DD                    - Filter from date
#        ?date_to=YYYY-MM-DD                      - Filter to date
#
# POST   /api/dashboard/feedback/submit/          - Public: candidate submits feedback
#
# GET    /api/dashboard/recruitment-costs/        - List recruitment costs
# POST   /api/dashboard/recruitment-costs/        - Create recruitment cost
# GET    /api/dashboard/recruitment-costs/{id}/   - Get cost detail
# PUT    /api/dashboard/recruitment-costs/{id}/   - Update cost
# DELETE /api/dashboard/recruitment-costs/{id}/   - Delete cost
