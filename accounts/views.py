from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Company, MagicLink
from .serializers import (
    CompanySignupSerializer, UserSerializer, CreateUserSerializer,
    SetPinSerializer, PinLoginSerializer, MagicLinkSerializer
)
from .permissions import IsAdmin, IsAdminOrHRManager
from django.http import HttpResponse

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
    base_url = getattr(settings, 'FRONTEND_URL', 'https://hrmprod-apagecadd0adfng8.centralindia-01.azurewebsites.net')
    magic_link_url = f"{base_url}/accounts/api/set-pin?token={magic_link.token}"
    
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
    permission_classes = [permissions.IsAuthenticated, IsAdminOrHRManager]
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