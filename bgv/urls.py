# bgv/urls.py

from rest_framework.routers import DefaultRouter

from django.urls import path, include

from .views import CandidateBGVViewSet


router = DefaultRouter()

router.register(
    "candidate-bgv",
    CandidateBGVViewSet,
    basename="candidate-bgv"
)

urlpatterns = [
    path("", include(router.urls)),
]