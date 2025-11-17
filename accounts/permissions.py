from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Permission class for Admin users only"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsAdminOrHRManager(permissions.BasePermission):
    """Permission class for Admin or HR Manager users"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'hr_manager']
        )


class IsHRManager(permissions.BasePermission):
    """Permission class for HR Manager users only"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'hr_manager'


class IsHR(permissions.BasePermission):
    """Permission class for HR users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'hr'


class IsDepartmentHead(permissions.BasePermission):
    """Permission class for Department Head users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'department_head'


class IsConsultancy(permissions.BasePermission):
    """Permission class for Consultancy users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'consultancy'


class IsSameCompany(permissions.BasePermission):
    """Permission to ensure users can only access data from their company"""
    
    def has_object_permission(self, request, view, obj):
        # Check if object has a company attribute
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        
        # Check if object is a user
        if hasattr(obj, 'user') and hasattr(obj.user, 'company'):
            return obj.user.company == request.user.company
        
        return False


class CanCreateUsers(permissions.BasePermission):
    """Permission for users who can create other users"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_create_users()
        )