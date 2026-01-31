from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Company, MagicLink
from .serializers import (
    CompanySignupSerializer, UserSerializer, CreateUserSerializer, UpdateMyProfileSerializer,
    SetPinSerializer, PinLoginSerializer, MagicLinkSerializer
)
from .permissions import IsAdmin, IsAdminOrHRManager,IsDepartmentHead
from django.http import HttpResponse
from django.utils import timezone

def home(request):
    return HttpResponse("Welcome to the HRMS KnowCraft Application!")

def get_tokens_for_user(user):
    """Generate JWT tokens with custom claims including role"""
    refresh = RefreshToken.for_user(user)
    
    # Add custom claims
    refresh['role'] = user.role
    refresh['company_id'] = str(user.company.id)
    refresh['name'] = user.name
    
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def send_magic_link_email(user, magic_link):
    """Send magic link email to user"""
    base_url = getattr(settings, 'FRONTEND_URL', 'https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net')
    magic_link_url = f"{base_url}/otp-set?token={magic_link.token}"
    # magic_link_url = f"{base_url}/api/accounts/set-pin?token={magic_link.token}"
    
    subject = f"Set Your PIN - {user.company.name}"
    message = f"""
    Hello {user.name},
    
    Your account has been created as {user.get_role_display()} at {user.company.name}.
    
    Please click the link below to set your 6-digit PIN:
    {magic_link_url}
    
    This link will expire in 24 hours.
    
    Best regards,
    {user.company.name} Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def send_forget_pin_email(user, magic_link):
    """Send forget pin email to user"""
    base_url = getattr(settings, 'FRONTEND_URL', 'https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net')
    magic_link_url = f"{base_url}/otp-set?token={magic_link.token}"
    # magic_link_url = f"{base_url}/api/accounts/set-pin?token={magic_link.token}"
    
    subject = f"ReSet Your PIN - {user.company.name}"
    message = f"""
    Hello {user.name},
        
    Please click the link below to reset your 6-digit PIN:
    {magic_link_url}
    
    This link will expire in 24 hours.
    
    Best regards,
    {user.company.name} Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

class CompanySignupView(APIView):
    """Company admin signup endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = CompanySignupSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            company = result['company']
            admin = result['admin']
            
            # Create magic link
            magic_link = MagicLink.create_link(admin, purpose='set_pin')
            
            # Send magic link email
            try:
                send_magic_link_email(admin, magic_link)
            except Exception as e:
                # Log error but don't fail the request
                print(f"Failed to send email: {e}")
            
            return Response({
                'message': 'Company registered successfully. Admin user created.',
                'company': {
                    'id': str(company.id),
                    'name': company.name,
                    'email': company.email
                },
                'admin': {
                    'id': str(admin.id),
                    'name': admin.name,
                    'email': admin.email,
                    'role': admin.role
                },
                'magic_link': MagicLinkSerializer(magic_link, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SetPinView(APIView):
    """Set 6-digit PIN using magic link"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = SetPinSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            return Response({
                'message': 'PIN set successfully. You can now login.',
                'user': {
                    'id': str(user.id),
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'company_id': str(user.company.id)
                },
                **tokens
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PinLoginView(APIView):
    """Login with email and 6-digit PIN"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PinLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': str(user.id),
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'role_display': user.get_role_display(),
                    'company_id': str(user.company.id),
                    'company_name': user.company.name
                },
                **tokens
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateUserView(APIView):
    """Create new user (Admin/HR Manager only)"""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrHRManager]
    
    def post(self, request):
        serializer = CreateUserSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Create user
            user = User.objects.create_user(
                email=serializer.validated_data['email'],
                name=serializer.validated_data['name'],
                company=request.user.company,
                role=serializer.validated_data['role']
            )
            user.created_by = request.user
            user.save()
            
            # Create magic link
            magic_link = MagicLink.create_link(user, purpose='set_pin')
            
            # Send magic link email
            try:
                send_magic_link_email(user, magic_link)
            except Exception as e:
                print(f"Failed to send email: {e}")
            
            return Response({
                'message': 'User created successfully. Magic link sent to email.',
                'user': UserSerializer(user).data,
                'magic_link': MagicLinkSerializer(magic_link, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    """List all users in the company"""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrHRManager | IsDepartmentHead]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        # Only show users from the same company
        return User.objects.filter(company=self.request.user.company)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a user"""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrHRManager]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        # Only access users from the same company
        return User.objects.filter(company=self.request.user.company)


class CurrentUserView(APIView):
    """Get current authenticated user details"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'id': str(user.id),
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'role_display': user.get_role_display(),
            'company_id': str(user.company.id),
            'company_name': user.company.name,
            'pin_set': user.pin_set,
            'is_active': user.is_active
        })

class UpdateMyProfileView(APIView):
    """
    Allow logged-in user to update their own profile
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        user = request.user
        serializer = UpdateMyProfileSerializer(
            user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': {
                    'id': str(user.id),
                    'name': user.name,
                    'email': user.email
                }
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendMagicLinkView(APIView):
    """Resend magic link to a user"""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrHRManager]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id, company=request.user.company)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found in your company.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create new magic link
        magic_link = MagicLink.create_link(user, purpose='reset_pin')
        
        # Send email
        try:
            send_magic_link_email(user, magic_link)
        except Exception as e:
            return Response(
                {'error': f'Failed to send email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'message': 'Magic link sent successfully.',
            'magic_link': MagicLinkSerializer(magic_link, context={'request': request}).data
        }, status=status.HTTP_200_OK)
        
class ForgotPasswordView(APIView):
    """
    Public endpoint: accepts email (and optionally company identifier)
    and sends a reset magic link if a matching user exists.
    """

    permission_classes = [permissions.AllowAny]
    # throttle_classes = [AnonRateThrottle]   # enable in settings or here

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        company_id = request.data.get("company_id")  # optional: use if your app is multi-tenant
        # Alternatively accept company_domain or subdomain depending on your app design

        if not email:
            return Response({"error": "Email is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Optional: Validate email format here or via serializer

        # Look up user(s) - avoid leaking whether email exists in response
        qs = User.objects.filter(email=email)
        if company_id:
            qs = qs.filter(company_id=company_id)

        # If you support multiple users with same email, decide policy (e.g., send to all)
        user = qs.first()

        if user:
            # Optional: check brute-force / resend throttle per-account
            # Example simple check: if last_magic_sent_at within last X seconds/minutes -> skip/send limited
            last_sent = getattr(user, "last_magic_sent_at", None)
            cooldown_seconds = getattr(settings, "MAGIC_LINK_RESEND_COOLDOWN_SECONDS", 120)
            if last_sent and (timezone.now() - last_sent).total_seconds() < cooldown_seconds:
                # Don't indicate too much - respond as if request succeeded
                # You may also log the attempt for admin auditing
                pass
            else:
                # Create a reset magic link (single-use, short expiry)
                magic_link = MagicLink.create_link(user, purpose='reset_pin')
                try:
                    send_forget_pin_email(user, magic_link)
                    # Save last sent timestamp (simple anti-abuse)
                    user.last_magic_sent_at = timezone.now()
                    user.save(update_fields=["last_magic_sent_at"])
                except Exception as e:
                    # Log internally; do not reveal exception details to the caller
                    # (but you may choose to return 500 if you prefer)
                    # logger.exception("Failed sending magic link email")
                    pass

        # Always return a generic success response so callers can't enumerate accounts
        return Response(
            {"message": "If an account with that email exists, a reset link has been sent."},
            status=status.HTTP_200_OK
        )