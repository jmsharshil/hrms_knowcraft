from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardAPIView,
    AnalyticsAPIView,
    AdminAnalyticsAPIView,
    HRManagerAnalyticsAPIView,
    HRAnalyticsAPIView,
    DeptHeadAnalyticsAPIView,
    ConsultancyAnalyticsAPIView,
    RecruitmentCostViewSet,
    CandidateExperienceFeedbackSubmitView,
)

router = DefaultRouter()
router.register(r'recruitment-costs', RecruitmentCostViewSet, basename='recruitment-cost')

urlpatterns = [
    # Single dashboard endpoint returning all 10 metrics
    path('', DashboardAPIView.as_view(), name='dashboard'),

    # Comprehensive analytics endpoint (dispatcher)
    path('analytics/', AnalyticsAPIView.as_view(), name='analytics'),

    # Role-specific analytics endpoints
    path('analytics/admin/', AdminAnalyticsAPIView.as_view(), name='analytics-admin'),
    path('analytics/hr-manager/', HRManagerAnalyticsAPIView.as_view(), name='analytics-hr-manager'),
    path('analytics/hr/', HRAnalyticsAPIView.as_view(), name='analytics-hr'),
    path('analytics/dept-head/', DeptHeadAnalyticsAPIView.as_view(), name='analytics-dept-head'),
    path('analytics/consultancy/', ConsultancyAnalyticsAPIView.as_view(), name='analytics-consultancy'),

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
# GET    /api/dashboard/analytics/                - Dispatched analytics based on user role
# GET    /api/dashboard/analytics/admin/          - Full analytics (Admin only)
# GET    /api/dashboard/analytics/hr-manager/     - Full analytics (HR Manager only)
# GET    /api/dashboard/analytics/hr/             - Focused: CVs, Pipeline, Interviews, KPIs
# GET    /api/dashboard/analytics/dept-head/      - Focused: MRFs, Jobs, Pipeline, KPIs (by Dept)
# GET    /api/dashboard/analytics/consultancy/    - Focused: Their CVs, Pipeline, KPIs
#
#        ?date_from=YYYY-MM-DD                    - Filter from date
#        ?date_to=YYYY-MM-DD                      - Filter to date
#        ?department=<uuid>                       - Filter by department
#        ?job_id=<uuid>                           - Filter by job
#        ?hr_id=<uuid>                            - Filter by HR
#        ?source=<source>                         - Filter by source (e.g., linkedin)
#        ?sections=mrf,job,...                    - Optional: comma-separated list of sections
#
# POST   /api/dashboard/feedback/submit/          - Public: candidate submits feedback
#
# GET    /api/dashboard/recruitment-costs/        - List recruitment costs
# POST   /api/dashboard/recruitment-costs/        - Create recruitment cost
# GET    /api/dashboard/recruitment-costs/{id}/   - Get cost detail
# PUT    /api/dashboard/recruitment-costs/{id}/   - Update cost
# DELETE /api/dashboard/recruitment-costs/{id}/   - Delete cost
