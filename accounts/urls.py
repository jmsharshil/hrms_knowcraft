from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CompanySignupView, SetPinView, PinLoginView, CreateUserView,
    UserListView, UserDetailView, CurrentUserView, ResendMagicLinkView
)

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('signup/', CompanySignupView.as_view(), name='company-signup'),
    path('set-pin/', SetPinView.as_view(), name='set-pin'),
    path('login/', PinLoginView.as_view(), name='pin-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # User management endpoints
    path('users/create/', CreateUserView.as_view(), name='create-user'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<uuid:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/me/', CurrentUserView.as_view(), name='current-user'),
    path('users/resend-magic-link/', ResendMagicLinkView.as_view(), name='resend-magic-link'),
]