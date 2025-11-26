from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, DesignationViewSet, MRFViewSet, ApprovalWorkflowViewSet

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'designations', DesignationViewSet, basename='designation')
router.register(r'workflows', ApprovalWorkflowViewSet, basename='workflow')
router.register(r'mrfs', MRFViewSet, basename='mrf')

urlpatterns = [
    path('', include(router.urls)),
]