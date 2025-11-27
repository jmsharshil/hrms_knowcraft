from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.db import transaction

from .models import (
    Department, Designation, MRF, MRFApproval, 
    ApprovalWorkflow, WorkflowTemplate
)
from .serializers import (
    DepartmentSerializer, DesignationSerializer, MRFListSerializer,
    MRFDetailSerializer, MRFCreateUpdateSerializer, MRFApproveRejectSerializer,
    MRFSubmitSerializer, ApprovalWorkflowSerializer, WorkflowTemplateSerializer,
    WorkflowTemplateSummarySerializer
)
from .permissions import (
    CanManageMasterData, CanManageWorkflow, CanViewMRF, CanEditMRF,
    CanApproveMRF, CanSubmitMRF, IsDepartmentHead
)


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing departments"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, CanManageMasterData]
    
    def get_queryset(self):
        queryset = Department.objects.all()
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class DesignationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing designations"""
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    permission_classes = [IsAuthenticated, CanManageMasterData]
    
    def get_queryset(self):
        queryset = Designation.objects.all()
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class WorkflowTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing workflow templates"""
    queryset = WorkflowTemplate.objects.all()
    permission_classes = [IsAuthenticated, CanManageWorkflow]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return WorkflowTemplateSummarySerializer
        return WorkflowTemplateSerializer
    
    def get_queryset(self):
        queryset = WorkflowTemplate.objects.prefetch_related('levels')
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        is_default = self.request.query_params.get('is_default')
        if is_default is not None:
            queryset = queryset.filter(is_default=is_default.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanManageWorkflow])
    def set_as_default(self, request, pk=None):
        """Set this workflow as default"""
        workflow = self.get_object()
        
        # Remove default from all others
        WorkflowTemplate.objects.filter(is_default=True).update(is_default=False)
        
        # Set this as default
        workflow.is_default = True
        workflow.save()
        
        serializer = WorkflowTemplateSerializer(workflow)
        return Response({
            'message': f'{workflow.name} is now the default workflow',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class ApprovalWorkflowViewSet(viewsets.ModelViewSet):
    """ViewSet for managing individual workflow levels"""
    queryset = ApprovalWorkflow.objects.all()
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [IsAuthenticated, CanManageWorkflow]
    
    def get_queryset(self):
        queryset = ApprovalWorkflow.objects.select_related('template')
        
        template_id = self.request.query_params.get('template')
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class MRFViewSet(viewsets.ModelViewSet):
    """ViewSet for managing MRFs"""
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
            'department', 'designation', 'position_department', 
            'requested_by', 'workflow_template'
        ).prefetch_related('approvals', 'revisions', 'workflow_template__levels')
        
        # Filter based on user role
        if user.role == 'department_head':
            queryset = queryset.filter(
                Q(requested_by=user) | Q(status='approved')
            )
        elif user.role in ['admin', 'hr_manager', 'hr']:
            pass  # Can see all
        else:
            queryset = queryset.filter(status='approved')
        
        # Apply filters from query params
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        department_filter = self.request.query_params.get('department')
        if department_filter:
            queryset = queryset.filter(department_id=department_filter)
        
        workflow_filter = self.request.query_params.get('workflow')
        if workflow_filter:
            queryset = queryset.filter(workflow_template_id=workflow_filter)
        
        my_mrfs = self.request.query_params.get('my_mrfs')
        if my_mrfs and my_mrfs.lower() == 'true':
            queryset = queryset.filter(requested_by=user)
        
        pending_approval = self.request.query_params.get('pending_approval')
        if pending_approval and pending_approval.lower() == 'true':
            # Find workflow levels where user's role matches
            workflow_levels = ApprovalWorkflow.objects.filter(
                required_role=user.role,
                is_active=True
            ).values_list('template_id', 'level')
            
            # Build query for MRFs at those levels
            q_objects = Q()
            for template_id, level in workflow_levels:
                q_objects |= Q(
                    workflow_template_id=template_id,
                    current_approval_level=level - 1
                )
            
            queryset = queryset.filter(q_objects).filter(
                status__in=['pending_level_1', 'pending_level_2', 'pending_level_3']
            )
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanSubmitMRF])
    def submit(self, request, pk=None):
        """Submit MRF for approval"""
        mrf = self.get_object()
        
        if mrf.status not in ['draft', 'revision_required']:
            return Response(
                {'error': 'MRF can only be submitted from draft or revision_required status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get first approval level from MRF's workflow
        first_workflow = mrf.workflow_template.levels.filter(
            level=1,
            is_active=True
        ).order_by('order').first()
        
        if not first_workflow:
            return Response(
                {'error': f'Workflow template "{mrf.workflow_template.name}" has no active approval levels'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        mrf.status = 'pending_level_1'
        mrf.current_approval_level = 0
        mrf.submitted_at = timezone.now()
        mrf.save()
        
        serializer = MRFDetailSerializer(mrf, context={'request': request})
        return Response({
            'message': f'MRF submitted successfully using workflow: {mrf.workflow_template.name}',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @transaction.atomic
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApproveMRF])
    def approve_reject(self, request, pk=None):
        """Approve or reject MRF"""
        mrf = self.get_object()
        serializer = MRFApproveRejectSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action_type = serializer.validated_data['action']
        comments = serializer.validated_data.get('comments', '')
        rejection_reason = serializer.validated_data.get('rejection_reason', '')
        
        # Get current workflow level from MRF's workflow template
        next_level = mrf.current_approval_level + 1
        current_workflow = mrf.workflow_template.levels.filter(
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
                {'error': f'You do not have permission to approve at this level. Required role: {current_workflow.required_role}'},
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
            
            # Check if there's a next level in THIS workflow
            next_workflow = mrf.workflow_template.levels.filter(
                level=next_level + 1,
                is_active=True
            ).first()
            
            if next_workflow:
                # Move to next level
                mrf.current_approval_level = next_level
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
        """Get MRF statistics"""
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
            'pending_level_3': queryset.filter(status='pending_level_3').count(),
            'approved': queryset.filter(status='approved').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'revision_required': queryset.filter(status='revision_required').count(),
        }
        
        # Pending approval count for current user
        workflow_levels = ApprovalWorkflow.objects.filter(
            required_role=user.role,
            is_active=True
        ).values_list('template_id', 'level')
        
        q_objects = Q()
        for template_id, level in workflow_levels:
            q_objects |= Q(
                workflow_template_id=template_id,
                current_approval_level=level - 1
            )
        
        if q_objects:
            pending_for_user = MRF.objects.filter(q_objects).filter(
                status__in=['pending_level_1', 'pending_level_2', 'pending_level_3']
            ).count()
            stats['pending_my_approval'] = pending_for_user
        else:
            stats['pending_my_approval'] = 0
        
        return Response(stats, status=status.HTTP_200_OK)