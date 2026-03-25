from rest_framework import permissions


class IsDepartmentHead(permissions.BasePermission):
    """Only department heads can create MRFs"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'department_head'


class CanManageMasterData(permissions.BasePermission):
    """Admin and HR Manager can manage departments and designations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Read access for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write access only for admin and hr_manager
        return request.user.role in ['admin', 'hr_manager']


class CanManageWorkflow(permissions.BasePermission):
    """Only admin can manage approval workflow"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Read access for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write access only for admin
        return request.user.role in ['admin','department_head','hr_manager']   ## earlier it was 'admin'

class CanCreateMRF(permissions.BasePermission):
    """Control who can create MRFs"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin','department_head']
    
class CanViewMRF(permissions.BasePermission):
    """Control who can view MRFs"""
    
    def has_permission(self, request, view):
        # All authenticated users can list MRFs (filtered by role in view)
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Creator can always view
        if obj.requested_by == user:
            return True

        if obj.approvals.approver == user:
            return True
        
        # Approved MRFs visible to all authorized users
        if obj.status == 'approved':
            return True
        
        # HR and admin can view all
        if user.role in ['admin', 'hr_manager', 'hr']:
            return True
        
        # Approvers can view pending MRFs at their level
        if obj.can_user_approve(user):
            return True
        
        return False


class CanEditMRF(permissions.BasePermission):
    """Control who can edit MRFs"""
    
    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role in ['hr_manager','admin']:
            return True
        
        # Only creator can edit
        if obj.requested_by != user:
            return False
        
        # Can only edit in draft or revision_required status
        return obj.status in ['draft', 'revision_required']


class CanApproveMRF(permissions.BasePermission):
    """Control who can approve/reject MRFs"""
    
    def has_object_permission(self, request, view, obj):
        return obj.can_user_approve(request.user)


class CanSubmitMRF(permissions.BasePermission):
    """Control who can submit MRFs"""
    
    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role in ['hr_manager','admin']:
            return True
        
        # Only creator can submit
        if obj.requested_by != user:
            return False
        
        # Can only submit from draft or revision_required status
        return obj.status in ['draft', 'revision_required']
