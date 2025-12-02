from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, DesignationViewSet, MRFViewSet, 
    ApprovalWorkflowViewSet, WorkflowTemplateViewSet
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'designations', DesignationViewSet, basename='designation')
router.register(r'workflow-templates', WorkflowTemplateViewSet, basename='workflow-template')
router.register(r'workflow-levels', ApprovalWorkflowViewSet, basename='workflow-level')
router.register(r'mrfs', MRFViewSet, basename='mrf')

urlpatterns = [
    path('', include(router.urls)),
]