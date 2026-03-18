from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewSet, JobApplicationViewSet, JobApplicationLinkViewSet,ReferralApplicationViewSet, CareersViewSet, JobDropDownListViewSet, ApplicationViewSet

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'application-links', JobApplicationLinkViewSet, basename='application-link')
router.register(r'applications', JobApplicationViewSet, basename='application')
router.register(r'referral-applications', ReferralApplicationViewSet, basename='referral-application')
router.register(r'careers', CareersViewSet, basename='careers')
router.register(r'platform-applications', ApplicationViewSet, basename='platform-application')
router.register(r'job-dropdown', JobDropDownListViewSet, basename='job-dropdown')

urlpatterns = [
    path('', include(router.urls)),
]

# ============================================
# Available Endpoints
# ============================================

# JOBS:
# GET    /api/jobs/                               - List all jobs
# POST   /api/jobs/                               - Create job from MRF
# GET    /api/jobs/{id}/                          - Get job details
# PUT    /api/jobs/{id}/                          - Update job (INCLUDING PRIORITY)
# PATCH  /api/jobs/{id}/                          - Partial update job
# DELETE /api/jobs/{id}/                          - Delete job
# 
# POST   /api/jobs/{id}/assign_to_consultancy/    - Assign job to consultancy
# POST   /api/jobs/{id}/unassign_consultancy/     - Unassign from consultancy
# POST   /api/jobs/{id}/mark_position_filled/     - Mark one position as filled
# POST   /api/jobs/{id}/close_job/                - Close job (when all positions filled)
# POST   /api/jobs/{id}/reopen_job/               - Reopen closed job
# 
# GET    /api/jobs/statistics/                    - Get job statistics
# GET    /api/jobs/consultancy_list/              - Get list of consultancies
# 
# APPLICATION LINKS:
# GET    /api/application-links/                  - List all application links
# POST   /api/application-links/                  - Create new application link
# GET    /api/application-links/{id}/             - Get link details
# PUT    /api/application-links/{id}/             - Update link
# DELETE /api/application-links/{id}/             - Delete link
# 
# POST   /api/application-links/{id}/toggle_active/   - Activate/deactivate link
# GET    /api/application-links/{id}/track_view/      - Track link view (PUBLIC)
# GET    /api/application-links/statistics/           - Get link statistics
# 
# APPLICATIONS:
# GET    /api/applications/                       - List all applications
# POST   /api/applications/                       - Create application (internal)
# POST   /api/applications/public_apply/          - Public application endpoint
# GET    /api/applications/{id}/                  - Get application details
# PATCH  /api/applications/{id}/                  - Update application status
# DELETE /api/applications/{id}/                  - Delete application
# 
# GET    /api/applications/statistics/            - Get application statistics