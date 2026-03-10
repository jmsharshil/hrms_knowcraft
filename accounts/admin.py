from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Company, MagicLink


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'email']
    readonly_fields = ['id', 'created_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'name', 'role', 'company', 'phone', 'pin_set', 'is_active', 'created_at','department']
    list_filter = ['role', 'is_active', 'pin_set', 'created_at', 'company','department']
    search_fields = ['email', 'name', 'company__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']
    
    fieldsets = (
        (None, {'fields': ('email', 'pin', 'pin_set' ,'department')}),
        ('Personal Info', {'fields': ('name', 'role', 'company','phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
        ('Metadata', {'fields': ('id', 'created_by')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'company', 'is_active', 'is_staff','phone','department'),
        }),
    )
    
    ordering = ['-created_at']
    filter_horizontal = ('groups', 'user_permissions')


@admin.register(MagicLink)
class MagicLinkAdmin(admin.ModelAdmin):
    list_display = ['user', 'purpose', 'created_at', 'expires_at', 'used', 'is_valid_status']
    list_filter = ['purpose', 'used', 'created_at']
    search_fields = ['user__email', 'user__name', 'token']
    readonly_fields = ['id', 'token', 'created_at', 'used_at']
    
    def is_valid_status(self, obj):
        return obj.is_valid()
    is_valid_status.boolean = True
    is_valid_status.short_description = 'Valid'