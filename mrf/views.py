import io
import csv
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.negotiation import DefaultContentNegotiation
from django.utils import timezone
from django.db.models import Q, Case, When, Value, IntegerField
from django.db import transaction,IntegrityError
from django.http import HttpResponse
from slots.models import Interviewer
from jobs.models import Job, JobApplication
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from .models import (
    Department, Designation, MRF, MRFApproval, 
    ApprovalWorkflow, WorkflowTemplate, PrivateMRFApprovalLevel
)
from .serializers import (
    DepartmentSerializer, DesignationSerializer, MRFListSerializer,
    MRFDetailSerializer, MRFCreateUpdateSerializer, MRFApproveRejectSerializer,
    MRFSubmitSerializer, ApprovalWorkflowSerializer, WorkflowTemplateSerializer,
    WorkflowTemplateSummarySerializer,MRFHoldUnholdSerializer
)
from .permissions import (
    CanManageMasterData, CanManageWorkflow, CanViewMRF, CanEditMRF,
    CanApproveMRF, CanSubmitMRF, IsDepartmentHead,CanCreateMRF
)
from .utils import schedule_mrf_reminder
from onboarding.utils.sender import send_email,send_text
from .utils import email_templates, alt_text, is_valid_uuid
from accounts.models import User

class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing departments"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    # permission_classes = [IsAuthenticated, CanManageMasterData]

    def get_permissions(self):
        # Allow public access for list & retrieve
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]

        # Restrict create/update/delete
        return [IsAuthenticated(), CanManageMasterData()]
    
    def get_queryset(self):
        queryset = Department.objects.all()
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        user = self.request.user
        if hasattr(user, 'role') and user.role == "department_head" and hasattr(user, 'department') and hasattr(user.department,'id'):
            queryset = queryset.filter(id=user.department.id)
        
        if hasattr(user, 'company'):
            queryset = queryset.filter(company=user.company)
        return queryset
    
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'company'):
            serializer.save(company=user.company)
        else:
            serializer.save()

class DesignationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing designations"""
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    # permission_classes = [IsAuthenticated, CanManageMasterData]

    def get_permissions(self):
        # Allow public access for list & retrieve
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]

        # Restrict create/update/delete
        return [IsAuthenticated(), CanManageMasterData()]
    
    def get_queryset(self):
        queryset = Designation.objects.all()
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        user = self.request.user
        if hasattr(user, 'company'):
            queryset = queryset.filter(company=user.company)
        return queryset
    
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'company'):
            serializer.save(company=user.company)
        else:
            serializer.save()

class WorkflowTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing workflow templates"""
    queryset = WorkflowTemplate.objects.all()
    permission_classes = [IsAuthenticated, CanManageWorkflow]

    # Return full serializer by default (so list returns detailed info).
    # If client requests ?summary=true, we will return the lightweight serializer.
    def get_serializer_class(self):
        # If the client explicitly asks for a summary, return the summary serializer.
        if getattr(self, 'action', None) == 'list' and self.request is not None:
            if self.request.query_params.get('summary', '').lower() == 'true':
                return WorkflowTemplateSummarySerializer
            return WorkflowTemplateSerializer

        # For other actions (retrieve/create/update), use the detailed serializer
        # so retrieve returns levels too (you already support single GET by id).
        return WorkflowTemplateSerializer

    def get_queryset(self):
        # Prefetch levels to avoid N+1 on nested serialization
        queryset = WorkflowTemplate.objects.prefetch_related('levels')

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        is_default = self.request.query_params.get('is_default')
        if is_default is not None:
            queryset = queryset.filter(is_default=is_default.lower() == 'true')
        
        user = self.request.user
        # if hasattr(user, 'role') and user.role == "department_head" and hasattr(user, 'department') and hasattr(user.department,'id'):
        #     queryset = queryset.filter(department_id=user.department.id)
        
        if hasattr(user, 'company'):
            queryset = queryset.filter(company=user.company)
        return queryset

    # optional: explicit list override to clarify behavior / ensure ordering/pagination is used
    def list(self, request, *args, **kwargs):
        """
        GET /api/workflow-templates/
        Returns all workflow templates with nested levels (detailed) by default.
        Use ?summary=true to get the lightweight representation.
        """
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanManageWorkflow])
    def set_as_default(self, request, pk=None):
        """Set this workflow as default"""
        workflow = self.get_object()

        # Remove default from all others
        WorkflowTemplate.objects.filter(company=workflow.company,is_default=True).update(is_default=False)

        # Set this as default
        workflow.is_default = True
        workflow.save()

        serializer = WorkflowTemplateSerializer(workflow)
        return Response({
            'message': f'{workflow.name} is now the default workflow',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'company'):
            serializer.save(company=user.company)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            self.perform_destroy(instance)
        except IntegrityError:
            return Response(
                "Deletion not allowed. Workflow is used in MRFs.",
                status=status.HTTP_409_CONFLICT
            )
        
        return Response("Workflow Deleted Sucessfully!",status=status.HTTP_200_OK)

# class WorkflowTemplateViewSet(viewsets.ModelViewSet):
#     """ViewSet for managing workflow templates"""
#     queryset = WorkflowTemplate.objects.all()
#     permission_classes = [IsAuthenticated, CanManageWorkflow]
    
#     def get_serializer_class(self):
#         if self.action == 'list':
#             return WorkflowTemplateSummarySerializer
#         return WorkflowTemplateSerializer
    
#     def get_queryset(self):
#         queryset = WorkflowTemplate.objects.prefetch_related('levels')
        
#         is_active = self.request.query_params.get('is_active')
#         if is_active is not None:
#             queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
#         is_default = self.request.query_params.get('is_default')
#         if is_default is not None:
#             queryset = queryset.filter(is_default=is_default.lower() == 'true')
        
#         return queryset
    
#     @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanManageWorkflow])
#     def set_as_default(self, request, pk=None):
#         """Set this workflow as default"""
#         workflow = self.get_object()
        
#         # Remove default from all others
#         WorkflowTemplate.objects.filter(is_default=True).update(is_default=False)
        
#         # Set this as default
#         workflow.is_default = True
#         workflow.save()
        
#         serializer = WorkflowTemplateSerializer(workflow)
#         return Response({
#             'message': f'{workflow.name} is now the default workflow',
#             'data': serializer.data
#         }, status=status.HTTP_200_OK)


class ApprovalWorkflowViewSet(viewsets.ModelViewSet):
    """ViewSet for managing individual workflow levels"""
    queryset = ApprovalWorkflow.objects.all()
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [IsAuthenticated, CanManageWorkflow]
    
    def get_queryset(self):
        queryset = ApprovalWorkflow.objects.select_related('template')
        
        template_id = self.request.query_params.get('template')
        if template_id and is_valid_uuid(template_id):
            queryset = queryset.filter(template_id=template_id)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        user = self.request.user
        if hasattr(user, 'company'):
            queryset = queryset.filter(template__company=user.company)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'company'):
            serializer.save(company=user.company)
        else:
            serializer.save()

class MRFPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 200

class ExcelRenderer(BaseRenderer):
    media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    format = 'xlsx'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

class CSVRenderer(BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

class ExportContentNegotiator(DefaultContentNegotiation):
    def filter_renderers(self, renderers, format):
        fmt = (format or '').lower().strip()
        filtered = [r for r in renderers if getattr(r, 'format', None) == fmt]
        return filtered if filtered else renderers

class MRFViewSet(viewsets.ModelViewSet):
    """ViewSet for managing MRFs"""
    queryset = MRF.objects.all()
    serializer_class = MRFListSerializer
    pagination_class = MRFPagination
    permission_classes = [IsAuthenticated]
    content_negotiation_class = ExportContentNegotiator
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MRFListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MRFCreateUpdateSerializer
        elif self.action == 'submit':
            return MRFSubmitSerializer
        elif self.action == 'approve_reject':
            return MRFApproveRejectSerializer
        elif self.action == 'duplicate':
            return MRFCreateUpdateSerializer
        elif self.action in ['hold','unhold']:
            return MRFHoldUnholdSerializer
        return MRFDetailSerializer
    
    def get_permissions(self):
        if self.action in ['export', 'export_mrf_data']:
            return [AllowAny()]
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateMRF()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated()]
        elif self.action == 'submit':
            return [IsAuthenticated(), CanSubmitMRF()]
        elif self.action == 'approve_reject':
            return [IsAuthenticated(), CanApproveMRF()]
        elif self.action in ['hold', 'unhold','duplicate', 'mark_revision_required', 'request_revision']:
            return [IsAuthenticated(), CanEditMRF()]
        return [IsAuthenticated(), CanViewMRF()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = MRF.objects.select_related(
            'department', 'designation', 'position_department', 
            'requested_by', 'workflow_template'
        ).prefetch_related('approvals', 'revisions', 'workflow_template__levels',
                           'private_approval_levels', 'selected_viewers')
        
        # Also include private MRFs where user is an approver
        private_approver_q = Q(
            is_private=True,
            private_approval_levels__approver=user
        )
            
        # Filter based on user role
        if user.role in ['department_head','hr']:
            
            department_q = Q()
            if user.role == "department_head" and hasattr(user, 'department') and hasattr(user.department,'id'):
                department_q = Q(department_id=user.department.id)
            
            approval_workflows = ApprovalWorkflow.objects.filter(
                approver=user,
                is_active=True,
                template__company=user.company
            ).values_list('template_id', 'level')

            approval_q = Q()
            for template_id, level in approval_workflows:
                approval_q |= Q(
                    workflow_template_id=template_id,
                    current_approval_level=level - 1,
                    status__in=[
                        'pending_level_1',
                        'pending_level_2',
                        'pending_level_3'
                    ]
                )
            
            queryset = queryset.filter(
                Q(requested_by=user) | approval_q | department_q | private_approver_q
            )
        elif user.role in ['admin', 'hr_manager']:
            pass  # Can see all
        else:
            queryset = queryset.filter(status='approved')
        
        # Exclude private MRFs from unauthorized users
        # Admins and HR managers can see ALL MRFs (including private ones)
        if user.role not in ['admin', 'hr_manager']:
            queryset = queryset.filter(
                Q(is_private=False) |
                Q(is_private=True, requested_by=user) |
                Q(is_private=True, selected_viewers=user) |
                (Q(is_private=True, private_approval_levels__approver=user) & ~Q(status='draft'))
            )
        
        # Apply filters from query params
        status_filter = self.request.query_params.get('status')
        if status_filter:
            s_clean = status_filter.strip().lower()
            if s_clean == 'all_pending':
                queryset = queryset.filter(
                    status__in=['pending_level_1', 'pending_level_2', 'pending_level_3']
                )
            elif s_clean == 'pending_my_approval':
                # Pending approval count for current user
                workflow_levels = ApprovalWorkflow.objects.filter(
                    required_role=user.role,
                    is_active=True,
                    approver=user,
                    template__company=getattr(user, 'company', None)
                ).values_list('template_id', 'level')
                
                q_objects = Q()
                for template_id, level in workflow_levels:
                    q_objects |= Q(
                        workflow_template_id=template_id,
                        current_approval_level=level - 1
                    )
                
                if q_objects:
                    queryset = queryset.filter(q_objects).filter(
                        status__in=['pending_level_1', 'pending_level_2', 'pending_level_3']
                    )
                else:
                    queryset = queryset.none()
            elif s_clean not in ['all', '']:
                # Supports:
                # - open (open, assigned to internal hr/consultancy/both)
                # - on_hold / on hold
                # - filled
                # - joining_pending / joining pending
                # - comma-separated list of statuses, e.g. "open,joining_pending"
                status_list = [s.strip() for s in status_filter.split(',') if s.strip()]
                status_q = Q()
                for s in status_list:
                    s_norm = s.lower().replace(' ', '_')
                    if s_norm == 'open':
                        status_q |= (
                            Q(job__status__in=['open', 'assigned_to_consultancy', 'assigned_to_internal_hr', 'assigned_to_both']) |
                            Q(status='open') |
                            (Q(status='approved') & (Q(job__isnull=True) | Q(job__status__in=['open', 'assigned_to_consultancy', 'assigned_to_internal_hr', 'assigned_to_both'])))
                        )
                    elif s_norm == 'on_hold':
                        status_q |= (Q(status='on_hold') | Q(job__status='on_hold'))
                    elif s_norm == 'filled':
                        status_q |= (Q(status='filled') | Q(job__status='filled'))
                    elif s_norm == 'joining_pending':
                        status_q |= (Q(status='joining_pending') | Q(job__status='joining_pending'))
                    elif s_norm == 'closed':
                        status_q |= (Q(status='closed') | Q(job__status='closed'))
                    elif s_norm == 'cancelled':
                        status_q |= (Q(status='cancelled') | Q(job__status='cancelled'))
                    elif s_norm == 'all_pending':
                        status_q |= Q(status__in=['pending_level_1', 'pending_level_2', 'pending_level_3'])
                    else:
                        status_q |= (Q(status=s_norm) | Q(job__status=s_norm))
                queryset = queryset.filter(status_q)
        
        department_filter = self.request.query_params.get('department')
        if department_filter and department_filter != '' and is_valid_uuid(department_filter):
            queryset = queryset.filter(department_id=department_filter)

        designation_filter = self.request.query_params.get('designation')
        if designation_filter and designation_filter != '' and is_valid_uuid(designation_filter):
            queryset = queryset.filter(designation_id=designation_filter)
        
        department_name_filter = self.request.query_params.get('department_name')
        if department_name_filter and department_name_filter != '':
            queryset = queryset.filter(department__name__icontains=department_name_filter)

        designation_name_filter = self.request.query_params.get('designation_name')
        if designation_name_filter and designation_name_filter != '':
            queryset = queryset.filter(designation__name__icontains=designation_name_filter)
        
        workflow_filter = self.request.query_params.get('workflow')
        if workflow_filter and is_valid_uuid(workflow_filter):
            queryset = queryset.filter(workflow_template_id=workflow_filter)
        
        my_mrfs = self.request.query_params.get('my_mrfs')
        if my_mrfs and my_mrfs.lower() == 'true':
            queryset = queryset.filter(requested_by=user)
        
        pending_approval = self.request.query_params.get('pending_approval')
        if pending_approval and pending_approval.lower() == 'true':
            # Find workflow levels where user's role matches
            workflow_levels = ApprovalWorkflow.objects.filter(
                required_role=user.role,
                is_active=True,
                template__company=user.company
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
        
        if hasattr(user, 'company'):
            queryset = queryset.filter(company=user.company)

        # Default to active=True (consistent with soft-delete pattern);
        # ?is_active=false param retained for admin/HR-manager
        is_active_param = self.request.query_params.get('is_active')
        if is_active_param is not None:
            queryset = queryset.filter(is_active=is_active_param.lower() == 'true')
        else:
            queryset = queryset.filter(is_active=True)

        # General search filter
        search_param = (
            self.request.query_params.get('search') or
            self.request.query_params.get('q')
        )
        if search_param:
            search_param = search_param.strip()
            queryset = queryset.filter(
                Q(requisition_no__icontains=search_param) |
                Q(mrf_name__icontains=search_param) |
                Q(job__job_title__icontains=search_param) |
                Q(department__name__icontains=search_param) |
                Q(designation__name__icontains=search_param)
            )

        # Requisition number search filter
        requisition_no_filter = (
            self.request.query_params.get('requisition_no') or
            self.request.query_params.get('mrf_requisition_no') or
            self.request.query_params.get('mrf_reqisition_no')
        )
        if requisition_no_filter:
            queryset = queryset.filter(requisition_no__icontains=requisition_no_filter.strip())

        # Priority filter
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority__iexact=priority_filter.strip())

        # Job type filter
        job_type_filter = self.request.query_params.get('job_type')
        if job_type_filter:
            queryset = queryset.filter(job_type__iexact=job_type_filter.strip())

        # Date range filters (by creation date)
        from_date = self.request.query_params.get('from_date')
        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)

        to_date = self.request.query_params.get('to_date')
        if to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)

        # Annotate with priority to push joining_pending and filled to the end
        queryset = queryset.annotate(
            status_priority=Case(
                When(status__in=['joining_pending', 'filled'], then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).distinct().order_by('status_priority', '-created_at')

        return queryset
    
    @action(detail=True, methods=['get'], url_path='interviewers')
    def get_interviewers(self, request, pk=None):
        """
        Return all interviewers from this MRF.
        Auto-creates missing Interviewer entries so interviewer_id is NEVER null.
        """
        mrf = self.get_object()

        # Collect interviewer emails from MRF
        interviewer_emails = [
            mrf.interviewer_email_1,
            mrf.interviewer_email_2,
            mrf.interviewer_email_3,
            mrf.interviewer_email_final,
            mrf.interviewer_email_management_client
        ]

        interviewer_list = []

        for email in interviewer_emails:
            if not email:
                continue

            # Extract readable name from email prefix
            name = email.split("@")[0].replace(".", " ").title()

            # Ensure interviewer exists → auto-create if not found
            interviewer, created = Interviewer.objects.get_or_create(
                email=email,
                defaults={"name": name}
            )

            interviewer_list.append({
                "interviewer_id": str(interviewer.id),
                "name": interviewer.name,
                "email": interviewer.email
            })

        return Response({
            "mrf_id": str(mrf.id),
            "interviewers": interviewer_list
        }, status=200)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        """Submit MRF for approval"""
        mrf = self.get_object()
        
        if mrf.status not in ['draft', 'revision_required', 'rejected']:
            return Response(
                {'error': 'MRF can only be submitted from draft, revision_required, or rejected status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if mrf.company != getattr(request.user, 'company', None):
            return Response(
                {'error': 'You cannot modify MRFs from another company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if mrf.is_private:
            # Private MRF: validate direct approval levels exist
            first_level = mrf.private_approval_levels.filter(level=1, is_active=True).first()
            if not first_level:
                return Response(
                    {'error': 'No approval levels configured for this private MRF'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # Standard MRF: validate workflow template
            if not mrf.workflow_template:
                return Response(
                    {'error': 'No workflow template assigned to this MRF'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            first_workflow = mrf.workflow_template.levels.filter(
                level=1, is_active=True
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
        serializer = MRFSubmitSerializer(context={'mrf': mrf, 'request': request})
        serializer.submit()
        wf_name = 'Private' if mrf.is_private else mrf.workflow_template.name
        serializer = MRFDetailSerializer(mrf, context={'request': request})
        return Response({
            'message': f'MRF submitted successfully using workflow: {wf_name}',
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
        
        if mrf.company != getattr(request.user, 'company', None):
            return Response(
                {'error': 'You cannot modify MRFs from another company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        action_type = serializer.validated_data['action']
        comments = serializer.validated_data.get('comments', '')
        rejection_reason = serializer.validated_data.get('rejection_reason', '')
        
        # Get current workflow level
        next_level = mrf.current_approval_level + 1

        if mrf.is_private:
            # Private MRF: use direct approval levels
            current_private_level = mrf.private_approval_levels.filter(
                level=next_level, is_active=True
            ).first()
            if not current_private_level:
                return Response(
                    {'error': 'Approval level not found for current level'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Verify user is the designated approver
            if request.user.id != current_private_level.approver.id:
                return Response(
                    {'error': 'You are not the designated approver for this level'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            current_workflow = mrf.workflow_template.levels.filter(
                level=next_level, is_active=True
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
            # Create approval record (audit trail for both private and standard)
            MRFApproval.objects.create(
                mrf=mrf,
                level=next_level,
                approver=request.user,
                action='approved',
                comments=comments
            )
            
            if mrf.is_private:
                # Private MRF: check next direct approval level
                next_private_level = mrf.private_approval_levels.filter(
                    level=next_level + 1, is_active=True
                ).first()
                if next_private_level:
                    mrf.current_approval_level = next_level
                    mrf.status = f'pending_level_{next_level + 1}'
                else:
                    mrf.status = 'approved'
                    mrf.current_approval_level = next_level
                mrf.save()
                # NO notifications for private MRFs
                message = 'MRF approved successfully'
                if mrf.status == 'approved':
                    message = f'MRF fully approved. Requisition No: {mrf.requisition_no}'
            else:
                # Standard MRF: check next workflow level
                next_workflow = mrf.workflow_template.levels.filter(
                    level=next_level + 1, is_active=True
                ).first()
                
                if next_workflow:
                    mrf.current_approval_level = next_level
                    mrf.status = f'pending_level_{next_level + 1}'
                else:
                    mrf.status = 'approved'
                    mrf.current_approval_level = next_level
                
                mrf.save()

                if mrf.status.startswith("pending"):
                    # Send email to NEXT approver only
                    next_level = mrf.current_approval_level + 1
                    next_workflow = mrf.workflow_template.levels.filter(
                        level=next_level, is_active=True
                    ).select_related('approver').first()

                    if next_workflow:
                        approver = next_workflow.approver or User.objects.filter(
                            role=next_workflow.required_role,
                            company=mrf.company,
                            is_active=True
                        ).first()

                        if approver:
                            subject = f"Requisition Pending Approval – {mrf.designation.name}"
                            template = email_templates['mrf_submit_new'].format(
                                manager_name=approver.name,
                                hod_name=mrf.requested_by.name,
                                designation=mrf.designation.name,
                                date=mrf.created_at.strftime("%B %d, %Y")
                            )
                            text = alt_text['mrf_submit_new'].format(
                                manager_name=approver.name,
                                hod_name=mrf.requested_by.name,
                                designation=mrf.designation.name,
                                date=mrf.created_at.strftime("%B %d, %Y")
                            )
                            if not mrf.is_private:
                                send_email(to=approver.email, subject=subject, template=template, text=text, event="mrf_approval_request", email_type="internal")
                                if approver.phone:
                                    send_text(to=approver.phone, text=text)
                    schedule_mrf_reminder(mrf.id)

                message = 'MRF approved successfully'
                if mrf.status == 'approved':
                    subject = f"MRF Approved – {mrf.designation.name}"
                    template = email_templates['mrf_approved'].format(
                        manager_name=mrf.requested_by.name,
                        designation=mrf.designation.name,
                        date=mrf.approved_at.strftime("%B %d, %Y")
                    )
                    text = alt_text['mrf_approved'].format(
                        manager_name=mrf.requested_by.name,
                        designation=mrf.designation.name,
                        date=mrf.approved_at.strftime("%B %d, %Y")
                    )
                    if not mrf.is_private:
                        send_email(to=mrf.requested_by.email, subject=subject, template=template, text=text, event="mrf_approved", email_type="internal")
                        if mrf.requested_by.phone:
                            send_text(to=mrf.requested_by.phone, text=text)
                    message = f'MRF fully approved. Requisition No: {mrf.requisition_no}'
        
        else:  # reject
            now = timezone.now()
            # Create rejection record (audit trail for both private and standard)
            MRFApproval.objects.create(
                mrf=mrf,
                level=next_level,
                approver=request.user,
                action='rejected',
                comments=comments,
                rejection_reason=rejection_reason
            )
            
            mrf.status = 'rejected'
            mrf.rejected_at = now
            mrf.current_approval_level = 0
            mrf.save()
            
            if not mrf.is_private:
                # Send rejection notification only for standard MRFs
                subject = f"MRF Rejected – {mrf.designation.name}"
                template = email_templates['mrf_reject'].format(
                    manager_name=mrf.requested_by.name,
                    approver_name=request.user.name,
                    designation=mrf.designation.name,
                    date=mrf.rejected_at.strftime("%B %d, %Y")
                )
                text = alt_text['mrf_reject'].format(
                    manager_name=mrf.requested_by.name,
                    approver_name=request.user.name,
                    designation=mrf.designation.name,
                    date=mrf.rejected_at.strftime("%B %d, %Y")
                )
                send_email(to=mrf.requested_by.email, subject=subject, template=template, text=text, event="mrf_rejected", email_type="internal")
                if mrf.requested_by.phone:
                    send_text(to=mrf.requested_by.phone, text=text)
            
            message = 'MRF rejected. Department head can revise and resubmit.'
        
        serializer = MRFDetailSerializer(mrf, context={'request': request})
        return Response({
            'message': message,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_revision_required(self, request, pk=None):
        """
        Move a rejected MRF to 'revision_required' status so that the user
        can edit and resubmit it. Sends notification email.
        """
        mrf = self.get_object()

        if mrf.company != getattr(request.user, 'company', None):
            return Response(
                {'error': 'You cannot modify MRFs from another company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = request.user
        can_change = (
            user == mrf.requested_by or
            user.role in ['admin', 'hr_manager', 'hr', 'department_head']
        )
        if not can_change:
            return Response(
                {'error': 'You do not have permission to request revision for this MRF.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if mrf.status != 'rejected':
            return Response(
                {'error': f'Only rejected MRFs can be moved to revision required. Current status: {mrf.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        mrf.status = 'revision_required'
        mrf.save(update_fields=['status', 'updated_at'])

        # Send email notification
        if not mrf.is_private and mrf.requested_by and mrf.requested_by.email:
            desig_name = mrf.designation.name if mrf.designation else mrf.mrf_name
            subject = f"MRF Marked for Revision – {desig_name}"
            template = email_templates['mrf_revision_required'].format(
                manager_name=mrf.requested_by.name,
                designation=desig_name
            )
            text = alt_text['mrf_revision_required'].format(
                manager_name=mrf.requested_by.name,
                designation=desig_name
            )
            send_email(
                to=mrf.requested_by.email,
                subject=subject,
                template=template,
                text=text,
                event="mrf_revision_required",
                email_type="internal"
            )
            if mrf.requested_by.phone:
                send_text(to=mrf.requested_by.phone, text=text)

        serializer = MRFDetailSerializer(mrf, context={'request': request})
        return Response({
            'message': 'MRF status changed to revision required. It can now be revised and resubmitted.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='request_revision')
    def request_revision(self, request, pk=None):
        """Alias for mark_revision_required"""
        return self.mark_revision_required(request, pk=pk)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanEditMRF])
    def duplicate(self, request, pk=None):
        """Duplicate an existing MRF as a new draft"""
        original = self.get_object()

        if original.status == 'draft':
            return Response(
                {'error': 'Cannot duplicate a draft MRF. Create a new one instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if original.company != getattr(request.user, 'company', None):
            return Response(
                {'error': 'You cannot duplicate MRFs from another company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create new MRF instance with copied fields
        new_mrf = MRF(
            company=original.company,
            workflow_template=original.workflow_template,
            mrf_name=original.mrf_name,
            department=original.department,
            date_of_request=original.date_of_request,
            requested_by=original.requested_by,
            requested_by_name=original.requested_by_name,
            requested_by_designation=original.requested_by_designation,
            designation=original.designation,
            team=original.team,
            position_department=original.position_department,
            no_of_vacancies=original.no_of_vacancies,
            location=original.location,
            job_type=original.job_type,
            resigned_crafter_name=original.resigned_crafter_name,
            resigned_crafter_ecode=original.resigned_crafter_ecode,
            resigned_crafter_designation=original.resigned_crafter_designation,
            key_responsibility=original.key_responsibility,
            required_qualifications=original.required_qualifications,
            experience_range=original.experience_range,
            skills_competencies=original.skills_competencies,
            business_justification=original.business_justification,
            salary_range=original.salary_range,
            expected_date_of_joining=original.expected_date_of_joining,
            case_study_required=original.case_study_required,
            technical_interview_1=original.technical_interview_1,
            technical_interview_2=original.technical_interview_2,
            final_interview=original.final_interview,
            status='draft',
            priority=original.priority,
            current_approval_level=0,
        )

        new_mrf.save()  # Sets created_at, updated_at, and email fields

        # Copy interviewer relationships
        new_mrf.hr_interviewer = original.hr_interviewer
        new_mrf.case_study_interviewer = original.case_study_interviewer
        new_mrf.final_interviewer = original.final_interviewer
        new_mrf.management_client_interviewer = original.management_client_interviewer
        new_mrf.technical_interviewers.set(original.technical_interviewers.all())

        new_mrf.save()  # Update email fields based on new relationships

        # Date fields like submitted_at, approved_at, rejected_at, date_received, requisition_no remain None

        serializer = MRFDetailSerializer(new_mrf, context={'request': request})
        return Response({
            'message': 'MRF duplicated successfully as a new draft.',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApproveMRF])
    def hold(self, request, pk=None):
        """
        POST /api/mrf/{id}/hold/
        Put MRF on hold. Triggers Job sync and link deactivation.
        Optional body: {"reason": "Budget review needed"}
        """
        mrf = self.get_object()
        
        if mrf.status == 'on_hold':
            return Response({"detail": "MRF is already on hold."}, status=status.HTTP_400_BAD_REQUEST)
        
        if mrf.status == 'rejected':  # Prevent on terminal statuses
            return Response({"detail": "Cannot hold a rejected MRF."}, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason', '')  # Optional
        
        # Update via serializer for validation
        data = {'status': 'on_hold', 'hold_reason': reason}
        serializer = self.get_serializer(mrf,data=data,partial=True,
            context={
                'action_type': 'hold',
                'mrf': mrf,
                'request': request
            }
        )
        if serializer.is_valid():
            serializer.save()
            # Signal will handle Job sync
            return Response({
                "detail": f"MRF {mrf.mrf_name} put on hold.",
                "reason": reason if reason else "No reason provided",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # NEW: Unhold Action
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApproveMRF])
    def unhold(self, request, pk=None):
        """
        POST /api/mrf/{id}/unhold/
        Resume MRF from on hold. Restores previous status and syncs Job.
        Optional body: {"target_status": "pending_level_1"} (overrides previous)
        """
        mrf = self.get_object()
        
        if mrf.status != 'on_hold':
            return Response({"detail": "MRF is not on hold."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Default to previous_status or 'draft'
        target_status = request.data.get('target_status', mrf.previous_status or 'draft')
        
        if target_status not in dict(MRF.STATUS_CHOICES):
            return Response({"detail": f"Invalid target status: {target_status}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update via serializer
        data = {'target_status': target_status}
        serializer = self.get_serializer(mrf,data=data,partial=True,
            context={
                'action_type': 'unhold',
                'mrf': mrf,
                'request': request
            }
        )
        if serializer.is_valid():
            serializer.save()
            # Signal will handle Job resume and link reactivation
            return Response({
                "detail": f"MRF {mrf.mrf_name} resumed from hold.",
                "previous_status": mrf.previous_status,
                "new_status": target_status,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get MRF statistics"""
        user = request.user
        
        # Base queryset based on user role
        if user.role in ['department_head','hr']:
            queryset = MRF.objects.filter(requested_by=user,company=getattr(user, 'company', None))
        else:
            queryset = MRF.objects.filter(company=getattr(user, 'company', None))
        
        stats = {
            'total': queryset.count(),
            'draft': queryset.filter(status='draft').count(),
            'pending_level_1': queryset.filter(status='pending_level_1').count(),
            'pending_level_2': queryset.filter(status='pending_level_2').count(),
            'pending_level_3': queryset.filter(status='pending_level_3').count(),
            'approved': queryset.filter(status='approved').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'revision_required': queryset.filter(status='revision_required').count(),
            'on_hold': queryset.filter(status='on_hold').count(),
            'all_pending': queryset.filter(
                status__in=['pending_level_1', 'pending_level_2', 'pending_level_3']
            ).count()
        }
        
        # Pending approval count for current user
        workflow_levels = ApprovalWorkflow.objects.filter(
            required_role=user.role,
            is_active=True,
            approver=user,
            template__company=getattr(user, 'company', None)
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

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'company'):
            serializer.save(company=user.company)
        else:
            serializer.save()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = {"results": serializer.data}

        # Calculate statistics based on filtered queryset
        stats = {
            'total': queryset.count(),
            'draft': queryset.filter(status='draft').count(),
            'pending_level_1': queryset.filter(status='pending_level_1').count(),
            'pending_level_2': queryset.filter(status='pending_level_2').count(),
            'pending_level_3': queryset.filter(status='pending_level_3').count(),
            'approved': queryset.filter(status='approved').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'revision_required': queryset.filter(status='revision_required').count(),
            'on_hold': queryset.filter(status='on_hold').count(),
            'all_pending': queryset.filter(
                status__in=['pending_level_1','pending_level_2','pending_level_3']
            ).count()
        }

        # Pending approvals for current user
        user = request.user
        workflow_levels = ApprovalWorkflow.objects.filter(
            required_role=user.role,
            is_active=True,
            approver=user,
            template__company=getattr(user, 'company', None)
        ).values_list('template_id', 'level')

        q_objects = Q()
        for template_id, level in workflow_levels:
            q_objects |= Q(
                workflow_template_id=template_id,
                current_approval_level=level - 1
            )

        if q_objects:
            stats['pending_my_approval'] = queryset.filter(q_objects).filter(
                status__in=['pending_level_1','pending_level_2','pending_level_3']
            ).count()
        else:
            stats['pending_my_approval'] = 0

        data["statistics"] = stats

        return Response(data)

    @transaction.atomic
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanEditMRF])
    def force_close(self, request, pk=None):
        """Force close an MRF and its related job"""
        mrf = self.get_object()
        
        if mrf.status in ['closed', 'filled', 'cancelled']:
            return Response({'error': f'MRF is already {mrf.status}'}, status=status.HTTP_400_BAD_REQUEST)
            
        closure_notes = request.data.get('closure_notes', 'MRF closed')
        
        mrf.previous_status = mrf.status
        mrf.status = 'closed'
        mrf.save()
        
        # Sync with Job
        if hasattr(mrf, 'job') and mrf.job:
            job = mrf.job
            if job.status not in ['closed', 'filled', 'cancelled']:
                job.previous_status = job.status
                job.status = 'closed'
                job.closed_at = timezone.now()
                job.closed_by = request.user
                job.closure_notes = closure_notes
                job.is_active = False
                job.save()
                
                job.application_links.filter(is_active=True).update(is_active=False)
                
                from jobs.models import JobAssignmentHistory
                JobAssignmentHistory.objects.create(
                    job=job,
                    action='closed',
                    consultancy=job.assigned_to_consultancy,
                    performed_by=request.user,
                    notes=closure_notes
                )
                
        serializer = MRFDetailSerializer(mrf, context={'request': request})
        return Response({
            'message': 'MRF and associated Job force closed successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanEditMRF])
    def soft_delete(self, request, pk=None):
        """Soft delete an MRF (set is_active=False)"""
        mrf = self.get_object()
        if not mrf.is_active:
            return Response({"detail": "MRF is already soft deleted."}, status=status.HTTP_400_BAD_REQUEST)
        
        mrf.soft_delete()

        return Response({
            "message": "MRF soft deleted successfully",
            "id": str(mrf.id)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='export', renderer_classes=[ExcelRenderer, CSVRenderer, JSONRenderer])
    def export(self, request):
        """
        Export endpoint alias accessible at /api/mrf/mrfs/export/
        """
        return self.export_mrf_data(request)

    @action(detail=False, methods=['get'], url_path='export_mrf_data', renderer_classes=[ExcelRenderer, CSVRenderer, JSONRenderer])
    def export_mrf_data(self, request):
        """
        Export comprehensive MRF data with relevant Job details and Candidate pipeline metrics.

        Authentication:
          - Without auth token: returns ALL MRF data (no role/company restrictions).
          - With auth token: respects role-based filtering, company isolation, and private MRF checks.

        Supports status filtering:
          - 'open' (includes open, assigned to internal hr, assigned to consultancy, assigned to both)
          - 'on_hold'
          - 'filled'
          - 'joining_pending'
          - Comma-separated combinations (e.g. ?status=open,joining_pending)
          - All accessible MRFs (?status=all or omitted)
        Supports formats:
          - 'xlsx' (default: styled professional Excel workbook)
          - 'csv' (UTF-8 BOM encoded CSV)
          - 'json' (JSON response with total_count and results)
        """
        user = request.user

        # Unauthenticated: return all MRFs without role/company restrictions
        if not user or not user.is_authenticated:
            base_qs = MRF.objects.filter(is_active=True)

            # Apply status filter even for unauthenticated requests
            status_filter = request.query_params.get('status')
            if status_filter:
                s_clean = status_filter.strip().lower()
                if s_clean not in ['all', '']:
                    status_list = [s.strip() for s in status_filter.split(',') if s.strip()]
                    status_q = Q()
                    for s in status_list:
                        s_norm = s.lower().replace(' ', '_')
                        if s_norm == 'open':
                            status_q |= (
                                Q(job__status__in=['open', 'assigned_to_consultancy', 'assigned_to_internal_hr', 'assigned_to_both']) |
                                Q(status='open') |
                                (Q(status='approved') & (Q(job__isnull=True) | Q(job__status__in=['open', 'assigned_to_consultancy', 'assigned_to_internal_hr', 'assigned_to_both'])))
                            )
                        elif s_norm == 'on_hold':
                            status_q |= (Q(status='on_hold') | Q(job__status='on_hold'))
                        elif s_norm == 'filled':
                            status_q |= (Q(status='filled') | Q(job__status='filled'))
                        elif s_norm == 'joining_pending':
                            status_q |= (Q(status='joining_pending') | Q(job__status='joining_pending'))
                        elif s_norm == 'closed':
                            status_q |= (Q(status='closed') | Q(job__status='closed'))
                        elif s_norm == 'cancelled':
                            status_q |= (Q(status='cancelled') | Q(job__status='cancelled'))
                        else:
                            status_q |= (Q(status=s_norm) | Q(job__status=s_norm))
                    base_qs = base_qs.filter(status_q)

            queryset = base_qs.select_related(
                'department',
                'designation',
                'position_department',
                'requested_by',
                'held_by',
                'company',
                'job',
                'job__assigned_to_internal_hr',
                'job__assigned_to_consultancy',
                'job__closed_by',
                'job__posted_by',
            ).prefetch_related(
                'job__assigned_internal_hrs',
                'job__assigned_consultancies',
                'job__applications',
            ).distinct()
        else:
            # Authenticated: use role-based get_queryset()
            queryset = self.get_queryset().select_related(
                'department',
                'designation',
                'position_department',
                'requested_by',
                'held_by',
                'company',
                'job',
                'job__assigned_to_internal_hr',
                'job__assigned_to_consultancy',
                'job__closed_by',
                'job__posted_by',
            ).prefetch_related(
                'job__assigned_internal_hrs',
                'job__assigned_consultancies',
                'job__applications',
            ).distinct()

        export_rows = []
        for mrf in queryset:
            job = getattr(mrf, 'job', None)
            applications = list(job.applications.all()) if job else []

            # Application metrics
            total_apps = len(applications)
            shortlisted_count = sum(
                1 for app in applications
                if app.is_shortlisted or app.status in [
                    'shortlisted', 'technical_interview_1', 'technical_interview_2',
                    'final_interview', 'offer_pending', 'offer_sent',
                    'offer_accepted', 'joining_pending', 'joined'
                ]
            )
            joining_pending_count = sum(1 for app in applications if app.status == 'joining_pending')
            joined_count = sum(1 for app in applications if app.status == 'joined')

            # Candidate summaries
            joined_or_pending_list = []
            for app in applications:
                if app.status in ['joining_pending', 'joined', 'offer_accepted']:
                    doj_str = app.joining_date.strftime('%Y-%m-%d') if app.joining_date else 'No DOJ'
                    status_str = dict(JobApplication.STATUS_CHOICES).get(app.status, app.status.replace('_', ' ').title())
                    name_str = app.candidate_name or 'Unknown Candidate'
                    joined_or_pending_list.append(f"{name_str} ({status_str}, DOJ: {doj_str})")

            joined_or_pending_summary = "; ".join(joined_or_pending_list)
            all_candidates_summary = ", ".join([app.candidate_name for app in applications if app.candidate_name])

            # Assigned HRs
            assigned_hrs = []
            if job:
                if job.assigned_to_internal_hr:
                    hr_label = job.assigned_to_internal_hr.name or job.assigned_to_internal_hr.email
                    if hr_label:
                        assigned_hrs.append(hr_label)
                for u in job.assigned_internal_hrs.all():
                    hr_label = u.name or u.email
                    if hr_label and hr_label not in assigned_hrs:
                        assigned_hrs.append(hr_label)
            assigned_hrs_str = ", ".join(assigned_hrs)

            # Assigned Consultancies
            assigned_consults = []
            if job:
                if job.assigned_to_consultancy:
                    c_label = job.assigned_to_consultancy.name or job.assigned_to_consultancy.email
                    if c_label:
                        assigned_consults.append(c_label)
                for u in job.assigned_consultancies.all():
                    c_label = u.name or u.email
                    if c_label and c_label not in assigned_consults:
                        assigned_consults.append(c_label)
            assigned_consults_str = ", ".join(assigned_consults)

            # Vacancy & Filled counts
            vacancies = (job.no_of_positions if (job and job.no_of_positions is not None) else (mrf.no_of_vacancies or 0))
            filled = job.positions_filled if job else (vacancies if mrf.status == 'filled' else 0)
            remaining = max(0, vacancies - filled)

            # Display labels
            mrf_status_disp = dict(MRF.STATUS_CHOICES).get(mrf.status, (mrf.status or '').replace('_', ' ').title())
            job_status_disp = (
                dict(Job.JOB_STATUS_CHOICES).get(job.status, job.status.replace('_', ' ').title())
                if job else 'No Job Created'
            )

            # Format dates
            created_at_str = mrf.created_at.strftime('%Y-%m-%d %H:%M') if mrf.created_at else ''
            approved_at_str = mrf.approved_at.strftime('%Y-%m-%d %H:%M') if mrf.approved_at else ''
            req_date_str = mrf.date_of_request.strftime('%Y-%m-%d') if mrf.date_of_request else ''
            expected_doj_str = mrf.expected_date_of_joining.strftime('%Y-%m-%d') if mrf.expected_date_of_joining else ''
            expected_closure_str = job.expected_closure_date.strftime('%Y-%m-%d') if (job and job.expected_closure_date) else ''
            held_at_str = mrf.held_at.strftime('%Y-%m-%d %H:%M') if mrf.held_at else (job.held_at.strftime('%Y-%m-%d %H:%M') if (job and job.held_at) else '')
            closed_at_str = job.closed_at.strftime('%Y-%m-%d %H:%M') if (job and job.closed_at) else ''

            row = {
                "Requisition ID": mrf.requisition_no or "",
                "MRF Title": mrf.mrf_name or "",
                "MRF Status": mrf_status_disp,
                "Job Status": job_status_disp,
                "Department": mrf.department.name if mrf.department else (mrf.position_department.name if mrf.position_department else ""),
                "Designation": mrf.designation.name if mrf.designation else "",
                "Job Type": (mrf.job_type or "").replace('_', ' ').title(),
                "Priority": (mrf.priority or "").capitalize(),
                "Location": mrf.location or (job.location if job else ""),
                "No. of Vacancies": vacancies,
                "Positions Filled": filled,
                "Positions Remaining": remaining,
                "Experience Range": mrf.experience_range or (job.experience_range if job else ""),
                "Salary Range": mrf.salary_range or (job.salary_range if job else ""),
                "Expected Date of Joining": expected_doj_str,
                "Expected Closure Date": expected_closure_str,
                "Requested By": mrf.requested_by_name or (mrf.requested_by.name if mrf.requested_by else ""),
                "Requested By Email": mrf.requested_by.email if mrf.requested_by else "",
                "Requested By Designation": mrf.requested_by_designation or "",
                "Date of Request": req_date_str,
                "Created At": created_at_str,
                "Approved At": approved_at_str,
                "Current Approval Level": f"Level {mrf.current_approval_level}" if mrf.current_approval_level is not None else "",
                "Assigned Internal HR": assigned_hrs_str,
                "Assigned Consultancies": assigned_consults_str,
                "Total Applications": total_apps,
                "Shortlisted Candidates Count": shortlisted_count,
                "Joining Pending Count": joining_pending_count,
                "Joined Count": joined_count,
                "Joined / Joining Pending Candidates": joined_or_pending_summary,
                "All Candidates": all_candidates_summary,
                "Hold Reason": mrf.hold_reason or (job.hold_reason if job else ""),
                "Held At": held_at_str,
                "Held By": mrf.held_by.name if mrf.held_by else "",
                "Job Closed At": closed_at_str,
                "Job Closed By": job.closed_by.name if (job and job.closed_by) else "",
                "Job Closure Notes": job.closure_notes if job else "",
                "Replacement Crafter Name": mrf.resigned_crafter_name or "",
                "Replacement Crafter Ecode": mrf.resigned_crafter_ecode or "",
                "Replacement Crafter Designation": mrf.resigned_crafter_designation or "",
                "Skills & Competencies": mrf.skills_competencies or "",
                "Business Justification": mrf.business_justification or "",
                "MRF ID": str(mrf.id),
                "Job ID": str(job.id) if job else "",
            }
            export_rows.append(row)

        export_format = request.query_params.get('format', 'xlsx').lower().strip()
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")

        # JSON Format
        if export_format == 'json':
            return Response({
                "total_count": len(export_rows),
                "results": export_rows
            }, status=status.HTTP_200_OK)

        # CSV Format
        if export_format == 'csv':
            output = io.StringIO()
            fieldnames = list(export_rows[0].keys()) if export_rows else [
                "Requisition ID", "MRF Title", "MRF Status", "Job Status", "Department", "Designation"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for r in export_rows:
                writer.writerow(r)

            filename = f"mrf_export_{timestamp}.csv"
            response = HttpResponse(
                output.getvalue().encode('utf-8-sig'),
                content_type="text/csv; charset=utf-8"
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        # Default: Excel (.xlsx) Format
        wb = Workbook()
        ws = wb.active
        ws.title = "MRF & Job Export"

        headers = list(export_rows[0].keys()) if export_rows else [
            "Requisition ID", "MRF Title", "MRF Status", "Job Status", "Department",
            "Designation", "Job Type", "Priority", "Location", "No. of Vacancies",
            "Positions Filled", "Positions Remaining", "Total Applications"
        ]
        ws.append(headers)

        # Styling
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        data_font = Font(name="Calibri", size=10)
        data_alignment_left = Alignment(horizontal="left", vertical="center")
        data_alignment_center = Alignment(horizontal="center", vertical="center")
        data_alignment_right = Alignment(horizontal="right", vertical="center")

        thin_side = Side(border_style="thin", color="D1D5DB")
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
        alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

        # Style Header Row
        ws.row_dimensions[1].height = 28
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = cell_border

        numeric_headers = {
            "No. of Vacancies", "Positions Filled", "Positions Remaining",
            "Total Applications", "Shortlisted Candidates Count",
            "Joining Pending Count", "Joined Count"
        }
        center_headers = {
            "Requisition ID", "MRF Status", "Job Status", "Job Type",
            "Priority", "Expected Date of Joining", "Expected Closure Date",
            "Date of Request", "Created At", "Approved At", "Current Approval Level",
            "Held At", "Job Closed At"
        }

        # Write Data Rows
        for row_idx, data_dict in enumerate(export_rows, start=2):
            ws.row_dimensions[row_idx].height = 20
            is_alt = (row_idx % 2 == 0)
            row_values = [
                val if isinstance(val, (int, float, bool)) else (str(val) if val is not None else "")
                for val in (data_dict.get(h, "") for h in headers)
            ]
            ws.append(row_values)

            for col_idx, header_name in enumerate(headers, start=1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.font = data_font
                cell.border = cell_border
                if is_alt:
                    cell.fill = alt_fill

                if header_name in numeric_headers:
                    cell.alignment = data_alignment_right
                elif header_name in center_headers:
                    cell.alignment = data_alignment_center
                else:
                    cell.alignment = data_alignment_left

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if '\n' in val_str:
                    lines = val_str.split('\n')
                    line_len = max(len(l) for l in lines) if lines else 0
                    if line_len > max_len:
                        max_len = line_len
                elif len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(13, min(max_len + 4, 52))

        ws.freeze_panes = "A2"
        ws.views.sheetView[0].showGridLines = True

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"mrf_export_{timestamp}.xlsx"
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
        
            
