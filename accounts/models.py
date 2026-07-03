from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta


class Company(models.Model):
    """Multi-tenant company model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, email, company, role, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        if not company:
            raise ValueError('Company is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, company=company, role=role, **extra_fields)
        
        if password:
            user.set_password(password)
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create superuser (for Django admin)"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        # Create a default company for superuser
        company, _ = Company.objects.get_or_create(
            name='System Admin',
            defaults={'email': 'admin@system.local'}
        )
        
        user = self.create_user(email, company, password=password, **extra_fields)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with role-based access and multi-tenancy"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('hr_manager', 'HR Manager'),
        ('hr', 'HR'),
        ('department_head', 'Department Head'),
        ('consultancy', 'Consultancy'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')
    phone = models.CharField(null=True,blank=True)
    department = models.ForeignKey('mrf.department',null=True,blank=True,on_delete=models.CASCADE)
    
    # PIN for authentication (stored as hash)
    pin = models.CharField(max_length=128, null=True, blank=True)
    pin_set = models.BooleanField(default=False)
    
    # Django required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['email', 'company']
        indexes = [
            models.Index(fields=['company']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.email}) - {self.get_role_display()}"
    
    def has_role(self, *roles):
        """Check if user has any of the specified roles"""
        return self.role in roles
    
    def can_create_users(self):
        """Check if user can create other users"""
        return self.role in ['admin', 'hr_manager']

    def soft_delete(self):
        """Soft delete user (sets is_active=False). This disables login and filters from lists.
        Cascades via signals or views to assigned jobs/MRFs etc.
        """
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])


class MagicLink(models.Model):
    """Magic link for password-less authentication and PIN setup"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='magic_links')
    token = models.CharField(max_length=100, unique=True)
    purpose = models.CharField(max_length=20, choices=[
        ('set_pin', 'Set PIN'),
        ('reset_pin', 'Reset PIN'),
    ])
    
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Magic Link for {self.user.email} - {self.purpose}"
    
    def is_valid(self):
        """Check if magic link is still valid"""
        return not self.used and timezone.now() < self.expires_at
    
    def mark_used(self):
        """Mark magic link as used"""
        self.used = True
        self.used_at = timezone.now()
        self.save()
    
    @staticmethod
    def generate_token():
        """Generate a unique secure token"""
        return uuid.uuid4().hex
    
    @classmethod
    def create_link(cls, user, purpose='set_pin', expiry_hours=24):
        """Create a new magic link"""
        token = cls.generate_token()
        expires_at = timezone.now() + timedelta(hours=expiry_hours)
        
        return cls.objects.create(
            user=user,
            token=token,
            purpose=purpose,
            expires_at=expires_at
        )