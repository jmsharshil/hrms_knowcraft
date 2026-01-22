from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Company, MagicLink,Role
import re


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    # role_display = serializers.CharField(source='get_role_display', read_only=True)
    roles = serializers.SlugRelatedField(
        many=True,
        # read_only=True,
        slug_field="code",
        queryset=Role.objects.all(),
    )
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'roles',
            'company', 'company_name', 'pin_set', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'pin_set', 'created_at', 'updated_at']
        extra_kwargs = {
            'pin': {'write_only': True}
        }

    def update(self, instance, validated_data):
        roles = validated_data.pop("roles", None)
        request = self.context.get("request")

        # Prevent HR from assigning admin role
        if roles and request and not request.user.has_role("admin"):
            if any(role.code == "admin" for role in roles):
                raise serializers.ValidationError(
                    {"roles": "You are not allowed to assign admin role."}
                )

        # Update normal fields
        instance = super().update(instance, validated_data)

        # Update roles if provided
        if roles is not None:
            instance.roles.set(roles)

        return instance


class CompanySignupSerializer(serializers.Serializer):
    """Serializer for company admin signup"""
    company_name = serializers.CharField(max_length=255)
    company_email = serializers.EmailField()
    admin_name = serializers.CharField(max_length=255)
    admin_email = serializers.EmailField()
    
    def validate_company_email(self, value):
        if Company.objects.filter(email=value).exists():
            raise serializers.ValidationError("Company with this email already exists.")
        return value
    
    def validate_admin_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value
    
    def create(self, validated_data):
        # Create company
        company = Company.objects.create(
            name=validated_data['company_name'],
            email=validated_data['company_email']
        )
        
        # Create admin user
        admin = User.objects.create_user(
            email=validated_data['admin_email'],
            name=validated_data['admin_name'],
            company=company,
            roles=['admin']
        )
        
        return {
            'company': company,
            'admin': admin
        }


class CreateUserSerializer(serializers.Serializer):
    """Serializer for creating users by Admin/HR Manager"""
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    # role = serializers.ChoiceField(choices=[
    #     ('admin', 'Admin'),
    #     ('hr_manager', 'HR Manager'),
    #     ('hr', 'HR'),
    #     ('department_head', 'Department Head'),
    #     ('consultancy', 'Consultancy'),
    # ])
    roles = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )

    def validate_email(self, value):
        # Check if email exists in the same company
        request = self.context.get('request')
        if request and request.user:
            if User.objects.filter(email=value, company=request.user.company).exists():
                raise serializers.ValidationError("User with this email already exists in your company.")
        return value
    
    def validate(self, attrs):
        request = self.context.get("request")
        creator = request.user

        # primary_role = attrs["role"]
        # extra_roles = attrs.get("roles", [])

        # requested_roles = set([primary_role] + extra_roles)
        requested_roles = set(attrs["roles"])

        # Admin can assign anything
        if creator.has_role("admin"):
            return attrs

        # HR Manager rules
        if creator.has_role("hr_manager"):
            allowed = {"hr", "department_head", "consultancy"}
            if not requested_roles.issubset(allowed):
                raise serializers.ValidationError(
                    "HR Manager can only assign HR, Department Head, or Consultancy roles."
                )
            return attrs

        raise serializers.ValidationError("You are not allowed to create users.")

    def validate_roles(self, value):
        valid_roles = set(
            Role.objects.values_list("code", flat=True)
        )
        invalid = set(value) - valid_roles
        if invalid:
            raise serializers.ValidationError(
                f"Invalid role(s): {', '.join(invalid)}"
            )
        return value

class SetPinSerializer(serializers.Serializer):
    """Serializer for setting 6-digit PIN"""
    token = serializers.CharField()
    pin = serializers.CharField(min_length=6, max_length=6)
    
    def validate_pin(self, value):
        if not re.match(r'^\d{6}$', value):
            raise serializers.ValidationError("PIN must be exactly 6 digits.")
        return value
    
    def validate_token(self, value):
        try:
            magic_link = MagicLink.objects.get(token=value)
            if not magic_link.is_valid():
                raise serializers.ValidationError("This link has expired or been used.")
            self.context['magic_link'] = magic_link
        except MagicLink.DoesNotExist:
            raise serializers.ValidationError("Invalid token.")
        return value
    
    def save(self):
        magic_link = self.context['magic_link']
        user = magic_link.user
        
        # Hash and save PIN
        user.pin = make_password(self.validated_data['pin'])
        user.pin_set = True
        user.save()
        
        # Mark magic link as used
        magic_link.mark_used()
        
        return user


class PinLoginSerializer(serializers.Serializer):
    """Serializer for PIN-based login"""
    email = serializers.EmailField()
    pin = serializers.CharField(min_length=6, max_length=6)
    
    def validate_pin(self, value):
        if not re.match(r'^\d{6}$', value):
            raise serializers.ValidationError("PIN must be exactly 6 digits.")
        return value
    
    def validate(self, data):
        from django.contrib.auth.hashers import check_password
        
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        
        if not user.pin_set:
            raise serializers.ValidationError("PIN not set. Please use the magic link sent to your email.")
        
        if not check_password(data['pin'], user.pin):
            raise serializers.ValidationError("Invalid credentials.")
        
        data['user'] = user
        return data


class MagicLinkSerializer(serializers.ModelSerializer):
    magic_link_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MagicLink
        fields = ['id', 'token', 'purpose', 'created_at', 'expires_at', 'magic_link_url']
        read_only_fields = ['id', 'token', 'created_at', 'expires_at']
    
    def get_magic_link_url(self, obj):
        request = self.context.get('request')
        if request:
            # Generate full URL for magic link
            base_url = request.build_absolute_uri('/').rstrip('/')
            return f"{base_url}/api/accounts/set-pin/?token={obj.token}"
        return None
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    company_id = serializers.UUIDField(required=False, allow_null=True)