from rest_framework import permissions

class CanViewJobs(permissions.BasePermission):
    """
    Permission to view jobs
    - Admin, HR Manager can view all jobs
    - HR (internal HR) can view jobs assigned to them or jobs they posted (optional)
    - Department Head can view jobs related to their department
    - Consultancy can view jobs assigned to them or visible_to_consultancy=True
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admin and HR Manager can view all jobs
        if user.role in ['admin', 'hr_manager']:
            return True

        # Internal HR can only view jobs assigned to them OR jobs they posted
        if user.role == 'hr':
            # Allow if job assigned to this internal HR
            if obj.assigned_to_internal_hr == user:
                return True
            # Optionally allow if they posted the job themselves (keep or remove as needed)
            if obj.posted_by == user:
                return True
            return False

        # Department Head can view jobs from their department
        if user.role == 'department_head':
            if hasattr(user, 'headed_department') and obj.department == user.headed_department:
                return True
            return False

        # Consultancy can view assigned jobs or publicly visible jobs
        if user.role == 'consultancy':
            return obj.assigned_to_consultancy == user or obj.visible_to_consultancy

        return False


class CanCreateJobs(permissions.BasePermission):
    """
    Permission to create jobs
    Only Admin and HR Manager can create jobs from approved MRFs
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'hr_manager']
        )


class CanEditJobs(permissions.BasePermission):
    """
    Permission to edit jobs
    Admin and HR Manager can edit jobs
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'hr_manager']
        )
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        return user.role in ['admin', 'hr_manager']


class CanAssignToConsultancy(permissions.BasePermission):
    """
    Permission to assign jobs to consultancy
    Only Admin and HR Manager can assign
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'hr_manager']
        )


class CanCloseJobs(permissions.BasePermission):
    """
    Permission to close jobs
    Admin and HR Manager can close jobs
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'hr_manager']
        )


class CanSubmitApplications(permissions.BasePermission):
    """
    Permission to submit job applications
    - HR can submit for any job
    - Consultancy can submit only for assigned jobs
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['hr', 'hr_manager', 'admin', 'consultancy']
        )


class CanManageApplications(permissions.BasePermission):
    """
    Permission to manage (update status) applications
    Admin, HR Manager, and HR can manage applications
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'hr_manager', 'hr']
        )
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        return user.role in ['admin', 'hr_manager', 'hr']


class CanViewApplications(permissions.BasePermission):
    """
    Permission to view applications
    - Admin, HR Manager, HR can view all applications
    - Consultancy can view applications for jobs assigned to them
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admin, HR Manager, HR can view all
        if user.role in ['admin', 'hr_manager']:
            return True
        
        if user.role == 'hr':
            return obj.job.assigned_to_internal_hr == user
        
        # Consultancy can view applications for their assigned jobs
        if user.role == 'consultancy':
            return obj.job.assigned_to_consultancy == user
        
        return False