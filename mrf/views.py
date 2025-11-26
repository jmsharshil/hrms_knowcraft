from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.db import transaction

from .models import Department, Designation, MRF, MRFApproval, ApprovalWorkflow
from .serializers import (
    DepartmentSerializer, DesignationSerializer, MRFListSerializer,
    MRFDetailSerializer, MRFCreateUpdateSerializer, MRFApproveRejectSerializer,
    MRFSubmitSerializer, ApprovalWorkflowSerializer
)
from .permissions import (
    CanManageMasterData, CanManageWorkflow, CanViewMRF, CanEditMRF,
    CanApproveMRF, CanSubmitMRF, IsDepartmentHead
)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing departments
    
    List: GET /api/mrf/departments/
    Create: POST /api/mrf/departments/
    Retrieve: GET /api/mrf/departments/{id}/
    Update: PUT /api/mrf/departments/{id}/
    Partial Update: PATCH /api/mrf/departments/{id}/
    Delete: DELETE /api/mrf/departments/{id}/
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, CanManageMasterData]
    
    def get_queryset(self):
        queryset = Department.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class DesignationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing designations
    
    List: GET /api/mrf/designations/
    Create: POST /api/mrf/designations/
    Retrieve: GET /api/mrf/designations/{id}/
    Update: PUT /api/mrf/designations/{id}/
    Partial Update: PATCH /api/mrf/designations/{id}/
    Delete: DELETE /api/mrf/designations/{id}/
    """
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    permission_classes = [IsAuthenticated, CanManageMasterData]
    
    def get_queryset(self):
        queryset = Designation.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class ApprovalWorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing approval workflow
    
    List: GET /api/mrf/workflows/
    Create: POST /api/mrf/workflows/
    Retrieve: GET /api/mrf/workflows/{id}/
    Update: PUT /api/mrf/workflows/{id}/
    Partial Update: PATCH /api/mrf/workflows/{id}/
    Delete: DELETE /api/mrf/workflows/{id}/
    """
    queryset = ApprovalWorkflow.objects.all()
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [IsAuthenticated, CanManageWorkflow]
    
    def get_queryset(self):
        queryset = ApprovalWorkflow.objects.all()
        
        # Filter by workflow name
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name=name)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class MRFViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing MRFs
    
    List: GET /api/mrf/mrfs/
        Query params:
            - status: Filter by status (draft, pending_level_1, pending_level_2, approved, rejected, revision_required)
            - department: Filter by department ID
            - my_mrfs: true/false - Show only user's MRFs
            - pending_approval: true/false - Show MRFs pending user's approval
    
    Create: POST /api/mrf/mrfs/
    Retrieve: GET /api/mrf/mrfs/{id}/
    Update: PUT /api/mrf/mrfs/{id}/
    Partial Update: PATCH /api/mrf/mrfs/{id}/
    Delete: DELETE /api/mrf/mrfs/{id}/
    
    Submit: POST /api/mrf/mrfs/{id}/submit/
    Approve/Reject: POST /api/mrf/mrfs/{id}/approve_reject/
    """
    queryset = MRF.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MRFListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MRFCreateUpdateSerializer
        elif self.action == 'submit':
            return MRFSubmitSerializer
        elif self.action == 'approve_reject':
            return MRFApproveRejectSerializer
        return MRFDetailSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsDepartmentHead()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), CanEditMRF()]
        elif self.action == 'submit':
            return [IsAuthenticated(), CanSubmitMRF()]
        elif self.action == 'approve_reject':
            return [IsAuthenticated(), CanApproveMRF()]
        return [IsAuthenticated(), CanViewMRF()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = MRF.objects.select_related(
            'department', 'designation', 'position_department', 'requested_by'
        ).prefetch_related('approvals', 'revisions')
        
        # Filter based on user role
        if user.role == 'department_head':
            # Department heads see their own MRFs and approved ones
            queryset = queryset.filter(
                Q(requested_by=user) | Q(status='approved')
            )
        elif user.role in ['admin', 'hr_manager', 'hr']:
            # HR and admin see all MRFs
            pass
        else:
            # Other roles see only approved MRFs
            queryset = queryset.filter(status='approved')
        
        # Apply filters from query params
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        department_filter = self.request.query_params.get('department')
        if department_filter:
            queryset = queryset.filter(department_id=department_filter)
        
        my_mrfs = self.request.query_params.get('my_mrfs')
        if my_mrfs and my_mrfs.lower() == 'true':
            queryset = queryset.filter(requested_by=user)
        
        pending_approval = self.request.query_params.get('pending_approval')
        if pending_approval and pending_approval.lower() == 'true':
            # Show MRFs that are pending at user's approval level
            next_level = 1  # Start with level 1
            workflow = ApprovalWorkflow.objects.filter(
                name='MRF Approval Workflow',
                required_role=user.role,
                is_active=True
            ).first()
            
            if workflow:
                # Find MRFs where current_approval_level + 1 == workflow.level
                queryset = queryset.filter(
                    current_approval_level=workflow.level - 1
                ).filter(
                    Q(status='pending_level_1') | Q(status='pending_level_2')
                )
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanSubmitMRF])
    def submit(self, request, pk=None):
        """
        Submit MRF for approval
        
        POST /api/mrf/mrfs/{id}/submit/
        """
        mrf = self.get_object()
        
        if mrf.status not in ['draft', 'revision_required']:
            return Response(
                {'error': 'MRF can only be submitted from draft or revision_required status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get first approval level
        first_workflow = ApprovalWorkflow.objects.filter(
            name='MRF Approval Workflow',
            level=1,
            is_active=True
        ).order_by('order').first()
        
        if not first_workflow:
            return Response(
                {'error': 'Approval workflow not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        mrf.status = 'pending_level_1'
        mrf.current_approval_level = 0
        mrf.submitted_at = timezone.now()
        mrf.save()
        
        serializer = MRFDetailSerializer(mrf, context={'request': request})
        return Response({
            'message': 'MRF submitted successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @transaction.atomic
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApproveMRF])
    def approve_reject(self, request, pk=None):
        """
        Approve or reject MRF
        
        POST /api/mrf/mrfs/{id}/approve_reject/
        Body: {
            "action": "approve" or "reject",
            "comments": "Optional comments",
            "rejection_reason": "Required if rejecting"
        }
        """
        mrf = self.get_object()
        serializer = MRFApproveRejectSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action_type = serializer.validated_data['action']
        comments = serializer.validated_data.get('comments', '')
        rejection_reason = serializer.validated_data.get('rejection_reason', '')
        
        # Get current workflow level
        next_level = mrf.current_approval_level + 1
        current_workflow = ApprovalWorkflow.objects.filter(
            name='MRF Approval Workflow',
            level=next_level,
            is_active=True
        ).first()
        
        if not current_workflow:
            return Response(
                {'error': 'Approval workflow not found for current level'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify user has correct role
        if request.user.role != current_workflow.required_role:
            return Response(
                {'error': 'You do not have permission to approve at this level'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if action_type == 'approve':
            # Create approval record
            MRFApproval.objects.create(
                mrf=mrf,
                level=next_level,
                approver=request.user,
                action='approved',
                comments=comments
            )
            
            # Check if there's a next level
            next_workflow = ApprovalWorkflow.objects.filter(
                name='MRF Approval Workflow',
                level=next_level + 1,
                is_active=True
            ).first()
            
            if next_workflow:
                # Move to next level
                mrf.current_approval_level = next_level
                if next_level == 1:
                    mrf.status = 'pending_level_2'
                else:
                    mrf.status = f'pending_level_{next_level + 1}'
            else:
                # Final approval
                mrf.status = 'approved'
                mrf.current_approval_level = next_level
            
            mrf.save()
            
            message = 'MRF approved successfully'
            if mrf.status == 'approved':
                message = f'MRF fully approved. Requisition No: {mrf.requisition_no}'
        
        else:  # reject
            # Create rejection record
            MRFApproval.objects.create(
                mrf=mrf,
                level=next_level,
                approver=request.user,
                action='rejected',
                comments=comments,
                rejection_reason=rejection_reason
            )
            
            mrf.status = 'revision_required'
            mrf.current_approval_level = 0
            mrf.save()
            
            message = 'MRF rejected. Department head can revise and resubmit.'
        
        serializer = MRFDetailSerializer(mrf, context={'request': request})
        return Response({
            'message': message,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get MRF statistics
        
        GET /api/mrf/mrfs/statistics/
        """
        user = request.user
        
        # Base queryset based on user role
        if user.role == 'department_head':
            queryset = MRF.objects.filter(requested_by=user)
        else:
            queryset = MRF.objects.all()
        
        stats = {
            'total': queryset.count(),
            'draft': queryset.filter(status='draft').count(),
            'pending_level_1': queryset.filter(status='pending_level_1').count(),
            'pending_level_2': queryset.filter(status='pending_level_2').count(),
            'approved': queryset.filter(status='approved').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'revision_required': queryset.filter(status='revision_required').count(),
        }
        
        # Pending approval count for current user
        workflow = ApprovalWorkflow.objects.filter(
            name='MRF Approval Workflow',
            required_role=user.role,
            is_active=True
        ).first()
        
        if workflow:
            pending_for_user = MRF.objects.filter(
                current_approval_level=workflow.level - 1
            ).filter(
                Q(status='pending_level_1') | Q(status='pending_level_2')
            ).count()
            stats['pending_my_approval'] = pending_for_user
        
        return Response(stats, status=status.HTTP_200_OK)