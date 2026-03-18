from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Count, F
from django.utils import timezone
from django.db import transaction

from .models import Job, JobAssignmentHistory, JobApplication, JobApplicationLink,ReferralApplication,Application
from .serializers import (
    JobListSerializer, JobDetailSerializer, JobCreateSerializer,
    JobUpdateSerializer, AssignToConsultancySerializer, CloseJobSerializer,
    JobAssignmentHistorySerializer, JobApplicationSerializer,
    JobApplicationCreateSerializer, JobApplicationUpdateSerializer,
    JobApplicationLinkSerializer, JobApplicationLinkCreateSerializer,
    PublicJobApplicationCreateSerializer, AssignToInternalHRSerializer, AssignToBothSerializer,
    ReferralApplicationCreateSerializer,ReferralApplicationSerializer, ReferralToJobApplicationCreateSerializer,
    CareerToJobApplicationCreateSerializer,ApplicationSerializer,ApplicationCreateSerializer,
    ApplicationToJobSerializer,JobDropDownListSerializer
)
from .permissions import (
    CanViewJobs, CanCreateJobs, CanEditJobs, CanAssignToConsultancy,
    CanCloseJobs, CanSubmitApplications, CanManageApplications,
    CanViewApplications
)
from accounts.models import User
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from .filters import JobApplicationFilter
from .utils import send_job_assignment_email
from mrf.utils import is_valid_uuid

class JobViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Jobs"""
    
    queryset = Job.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return JobListSerializer
        elif self.action == 'create':
            return JobCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return JobUpdateSerializer
        elif self.action == 'assign_to_consultancy':
            return AssignToConsultancySerializer
        elif self.action == 'assign_to_internal_hr':   # NEW
            return AssignToInternalHRSerializer
        elif self.action == 'assign_to_both':     # 👈 NEW
            return AssignToBothSerializer
        elif self.action == 'close_job':
            return CloseJobSerializer
        return JobDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateJobs()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), CanEditJobs()]
        elif self.action in ['assign_to_consultancy', 'assign_to_internal_hr', 'assign_to_both']:
            return [IsAuthenticated(), CanAssignToConsultancy()]  # you can make a separate permission for internal HR if needed
        elif self.action == 'close_job':
            return [IsAuthenticated(), CanCloseJobs()]
        return [IsAuthenticated(), CanViewJobs()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Job.objects.select_related(
            'department', 'designation', 'mrf', 
            'assigned_to_consultancy', 'posted_by'
        ).prefetch_related('applications', 'history', 'application_links')
        
        if not user.is_authenticated:
            return queryset.filter(is_active=True)
        
        # Filter based on user role
        if user.role in ['admin', 'hr_manager']:
            # Can see all jobs
            pass
        elif user.role == 'department_head':
            # Can see jobs from their department
            if hasattr(user, 'headed_department'):
                queryset = queryset.filter(department=user.headed_department)
            else:
                queryset = queryset.none()
        elif user.role == 'hr':
            # Internal HR: only jobs assigned to them OR jobs they posted
            queryset = queryset.filter(
                Q(assigned_to_internal_hr=user) | Q(posted_by=user) | Q(assigned_internal_hrs=user)
            )
        elif user.role == 'consultancy':
            # Can see assigned jobs or publicly visible jobs
            queryset = queryset.filter(
                Q(assigned_to_consultancy=user) | Q(visible_to_consultancy=True) | Q(assigned_consultancies=user)
            )
        else:
            queryset = queryset.none()
        
        # Apply filters from query params
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        department_filter = self.request.query_params.get('department')
        if department_filter and is_valid_uuid(department_filter):
            queryset = queryset.filter(department_id=department_filter)
        
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        assigned_to_me = self.request.query_params.get('assigned_to_me')
        if assigned_to_me and assigned_to_me.lower() == 'true':
            if user.role == 'consultancy':
                queryset = queryset.filter(
                    Q(assigned_consultancies=user) | Q(assigned_to_consultancy=user)
                )
            elif user.role in ['hr', 'hr_manager']:
                queryset = queryset.filter(
                    Q(assigned_internal_hrs=user) | Q(assigned_to_internal_hr=user)
                )
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(job_title__icontains=search) |
                Q(mrf__requisition_no__icontains=search) |
                Q(location__icontains=search)
            )
        
        if hasattr(user, 'company'):
            queryset = queryset.filter(company=user.company)
        return queryset
    
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'company'):
            serializer.save(company=user.company)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanAssignToConsultancy])
    def assign_to_consultancy(self, request, pk=None):
        """Assign job to a consultancy"""
        job = self.get_object()
        serializer = AssignToConsultancySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        consultancy_ids = serializer.validated_data['consultancy_ids']

        notes = serializer.validated_data.get('notes', '')
        
        # Get consultancy user
        try:
            consultancies = User.objects.filter(id__in=consultancy_ids, role='consultancy', is_active=True,company=request.user.company)
        except User.DoesNotExist:
            return Response(
                {'error': 'Consultancy user not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if job can be assigned
        job.assigned_consultancies.add(*consultancies)

        # backward compatibility
        if not job.assigned_to_consultancy:
            job.assigned_to_consultancy = consultancies.first()
        
        # Check if reassigning
        action = 'assigned'
        if job.assigned_to_consultancy:
            action = 'reassigned'
        
        # Update job
        # job.assigned_to_consultancy = consultancy
        job.assigned_at = timezone.now()
        job.assigned_by = request.user
        job.status = 'assigned_to_consultancy'
        job.visible_to_consultancy = True
        job.save()
        
        # Create history record
        for consultancy in consultancies:
            JobAssignmentHistory.objects.create(
                job=job,
                action='assigned',
                consultancy=consultancy,
                performed_by=request.user,
                notes=notes
            )
            self._create_consultancy_link(job, consultancy)
            send_job_assignment_email(consultancy, job, request.user)
        serializer = JobDetailSerializer(job, context={'request': request})
        return Response({
            'message': f'Job successfully assigned to {", ".join([c.name for c in consultancies])}',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanAssignToConsultancy])
    def unassign_consultancy(self, request, pk=None):
        """Unassign job from consultancy"""
        job = self.get_object()
        
        if not job.assigned_to_consultancy:
            return Response(
                {'error': 'Job is not assigned to any consultancy'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultancy = job.assigned_to_consultancy
        notes = request.data.get('notes', '')
        
        # Update job
        job.assigned_to_consultancy = None
        job.assigned_at = None
        job.assigned_by = None
        job.status = 'open'
        job.save()
        
        # Create history record
        JobAssignmentHistory.objects.create(
            job=job,
            action='unassigned',
            consultancy=consultancy,
            performed_by=request.user,
            notes=notes
        )
        
        serializer = JobDetailSerializer(job, context={'request': request})
        return Response({
            'message': f'Job unassigned from {consultancy.full_name}',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanAssignToConsultancy])
    def assign_to_internal_hr(self, request, pk=None):
        """Assign job to an internal HR user"""
        job = self.get_object()
        serializer = AssignToInternalHRSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        internal_hr_ids = serializer.validated_data['internal_hr_ids']
        notes = serializer.validated_data.get('notes', '')

        # get user
        try:
            internal_hrs = User.objects.filter(id__in=internal_hr_ids,is_active=True,company=request.user.company)
        except User.DoesNotExist:
            return Response({'error': 'Internal HR user not found'}, status=status.HTTP_404_NOT_FOUND)

        job.assigned_internal_hrs.add(*internal_hrs)

        if not job.assigned_to_internal_hr:
            job.assigned_to_internal_hr = internal_hrs.first()

        action = 'assigned_internal'
        if job.assigned_to_internal_hr:
            action = 'reassigned_internal'

        # Update job
        # job.assigned_to_internal_hr = internal_hr
        job.assigned_internal_at = timezone.now()
        job.assigned_internal_by = request.user
        # job.status = 'assigned_to_internal_hr'
        if job.assigned_consultancies.exists():
            job.status = 'assigned_to_both'
        else:
            job.status = 'assigned_to_internal_hr'
        # Optionally: leave visible_to_consultancy unchanged; you might want to keep consultancy visibility false by default
        job.save()

        # Create history record
        for hr in internal_hrs:
            JobAssignmentHistory.objects.create(
                job=job,
                action='assigned_internal',
                consultancy=hr,
                performed_by=request.user,
                notes=notes
            )
            send_job_assignment_email(hr, job, request.user)
        serializer = JobDetailSerializer(job, context={'request': request})
        return Response({
            'message': f'Job successfully assigned to internal HRs {", ".join([i.name for i in internal_hrs])}',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanAssignToConsultancy])
    def unassign_internal_hr(self, request, pk=None):
        job = self.get_object()
        if not job.assigned_to_internal_hr:
            return Response({'error': 'Job is not assigned to any internal HR'}, status=status.HTTP_400_BAD_REQUEST)

        internal_hr = job.assigned_to_internal_hr
        notes = request.data.get('notes', '')

        job.assigned_to_internal_hr = None
        job.assigned_internal_at = None
        job.assigned_internal_by = None
        job.status = 'open'
        job.save()

        JobAssignmentHistory.objects.create(
            job=job,
            action='unassigned',
            consultancy=internal_hr,  # again reused field
            performed_by=request.user,
            notes=notes
        )

        serializer = JobDetailSerializer(job, context={'request': request})
        return Response({
            'message': f'Job unassigned from {internal_hr.full_name}',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanAssignToConsultancy])
    def assign_to_both(self, request, pk=None):
        """
        Assign job to BOTH a consultancy and an internal HR.
        This is intended to be used while the job is still 'open',
        so we don't change the behavior of your existing actions.
        """
        job = self.get_object()
        serializer = AssignToBothSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # consultancy_id = serializer.validated_data['consultancy_id']
        # internal_hr_id = serializer.validated_data['internal_hr_id']
        notes = serializer.validated_data.get('notes', '') or ''

        # --- Get consultancy user ---
        # try:
        #     consultancy = User.objects.get(
        #         id=consultancy_id,
        #         role='consultancy',
        #         company=request.user.company,
        #         is_active=True
        #     )
        # except User.DoesNotExist:
        #     return Response(
        #         {'error': 'Consultancy user not found'},
        #         status=status.HTTP_404_NOT_FOUND
        #     )

        # # --- Get internal HR user ---
        # try:
        #     internal_hr = User.objects.get(
        #         id=internal_hr_id,
        #         role__in=['hr', 'hr_manager'],
        #         company=request.user.company,
        #         is_active=True
        #     )
        # except User.DoesNotExist:
        #     return Response(
        #         {'error': 'Internal HR user not found'},
        #         status=status.HTTP_404_NOT_FOUND
        #     )

        # # --- Check if job can be assigned (reuse your existing logic) ---
        # if not (job.can_be_assigned_to_consultancy() and job.can_be_assigned_to_internal_hr()):
        #     return Response(
        #         {'error': 'Job cannot be assigned. It may be in wrong status or inactive'},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        consultancy_ids = serializer.validated_data.get('consultancy_ids', [])
        internal_hr_ids = serializer.validated_data.get('internal_hr_ids', [])

        consultancies = User.objects.filter(id__in=consultancy_ids, role='consultancy', company=request.user.company)
        internal_hrs = User.objects.filter(id__in=internal_hr_ids, role__in=['hr', 'hr_manager'], company=request.user.company)

        job.assigned_consultancies.add(*consultancies)
        job.assigned_internal_hrs.add(*internal_hrs)

        if not job.assigned_to_consultancy and consultancies.exists():
            job.assigned_to_consultancy = consultancies.first()

        if not job.assigned_to_internal_hr and internal_hrs.exists():
            job.assigned_to_internal_hr = internal_hrs.first()

        # Determine history actions
        consultancy_action = 'assigned'
        if job.assigned_to_consultancy:
            consultancy_action = 'reassigned'

        internal_action = 'assigned_internal'
        if job.assigned_to_internal_hr:
            internal_action = 'reassigned_internal'

        # --- Update job fields ---
        now = timezone.now()

        # job.assigned_to_consultancy = consultancy
        job.assigned_at = now
        job.assigned_by = request.user

        # job.assigned_to_internal_hr = internal_hr
        job.assigned_internal_at = now
        job.assigned_internal_by = request.user

        # Make it visible for consultancy
        job.visible_to_consultancy = True

        # You can choose status; 'in_progress' makes sense when both are working on it
        job.status = 'assigned_to_both'

        job.save()

        # --- Create history records (no change to ACTION_CHOICES) ---
        for consultancy in consultancies:
            JobAssignmentHistory.objects.create(
                job=job,
                action='assigned',
                consultancy=consultancy,
                performed_by=request.user,
                notes=notes
            )
            self._create_consultancy_link(job, consultancy)
            send_job_assignment_email(consultancy, job, request.user)

        for hr in internal_hrs:
            JobAssignmentHistory.objects.create(
                job=job,
                action='assigned_internal',
                consultancy=hr,
                performed_by=request.user,
                notes=notes
            )
            send_job_assignment_email(hr, job, request.user)
        job_data = JobDetailSerializer(job, context={'request': request}).data
        return Response(
            {
                'message': f'Job successfully assigned to consultancies {", ".join([c.name for c in consultancies])} and internal HRs {", ".join([h.name for h in internal_hrs])}',
                'data': job_data
            },
            status=status.HTTP_200_OK
        )
    
    @transaction.atomic
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanCloseJobs])
    def close_job(self, request, pk=None):
        """Close a job position"""
        job = self.get_object()
        serializer = CloseJobSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        closure_notes = serializer.validated_data.get('closure_notes', '')
        
        # Check if all positions are filled
        if job.positions_filled < job.no_of_positions:
            return Response(
                {
                    'error': f'Cannot close job. Only {job.positions_filled} of {job.no_of_positions} positions filled',
                    'remaining': job.remaining_positions()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.status = 'closed'
        job.closed_at = timezone.now()
        job.closed_by = request.user
        job.closure_notes = closure_notes
        job.is_active = False
        job.save()
        
        # Deactivate all application links
        job.application_links.filter(is_active=True).update(is_active=False)
        
        # Create history record
        JobAssignmentHistory.objects.create(
            job=job,
            action='closed',
            consultancy=job.assigned_to_consultancy,
            performed_by=request.user,
            notes=closure_notes
        )
        
        serializer = JobDetailSerializer(job, context={'request': request})
        return Response({
            'message': 'Job closed successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanEditJobs])
    def mark_position_filled(self, request, pk=None):
        """Mark one position as filled (increment positions_filled)"""
        job = self.get_object()
        application_id = request.data.get('application_id')
        
        if not application_id:
            return Response(
                {'error': 'application_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify application exists and belongs to this job
        try:
            application = JobApplication.objects.get(id=application_id, job=job)
        except JobApplication.DoesNotExist:
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if we can fill more positions
        if job.positions_filled >= job.no_of_positions:
            return Response(
                {'error': 'All positions are already filled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update application status
        application.status = 'joined'
        application.save()
        
        # Increment positions filled
        job.positions_filled += 1
        job.save()
        
        serializer = JobDetailSerializer(job, context={'request': request})
        return Response({
            'message': f'Position marked as filled. {job.remaining_positions()} positions remaining',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanEditJobs])
    def reopen_job(self, request, pk=None):
        """Reopen a closed/cancelled job"""
        job = self.get_object()
        
        if job.status not in ['closed', 'cancelled']:
            return Response(
                {'error': 'Only closed or cancelled jobs can be reopened'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notes = request.data.get('notes', '')
        
        # Reset job status
        job.status = 'open'
        job.is_active = True
        job.closed_at = None
        job.closed_by = None
        job.closure_notes = ''
        job.save()
        
        # Create history record
        JobAssignmentHistory.objects.create(
            job=job,
            action='reopened',
            performed_by=request.user,
            notes=notes
        )
        
        serializer = JobDetailSerializer(job, context={'request': request})
        return Response({
            'message': 'Job reopened successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get job statistics"""
        user = request.user
        
        # Base queryset based on user role
        if user.role in ['admin', 'hr_manager', 'hr']:
            queryset = Job.objects.all()
        elif user.role == 'department_head':
            if hasattr(user, 'headed_department'):
                queryset = Job.objects.filter(department=user.headed_department)
            else:
                queryset = Job.objects.none()
        elif user.role == 'consultancy':
            queryset = Job.objects.filter(
                Q(assigned_to_consultancy=user) | Q(visible_to_consultancy=True) | Q(assigned_consultancies=user)
            )
        else:
            queryset = Job.objects.none()
        
        if hasattr(user, 'company'):
            queryset = queryset.filter(company=user.company)
        
        stats = {
            'total': queryset.count(),
            'open': queryset.filter(status='open').count(),
            'assigned_to_consultancy': queryset.filter(status='assigned_to_consultancy').count(),
            'assigned_to_both': queryset.filter(status='assigned_to_both').count(),
            'in_progress': queryset.filter(status='in_progress').count(),
            'filled': queryset.filter(status='filled').count(),
            'closed': queryset.filter(status='closed').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
            'active': queryset.filter(is_active=True).count(),
        }
        
        # Additional stats for consultancy
        if user.role == 'consultancy':
            stats['assigned_to_me'] = queryset.filter(assigned_to_consultancy=user).count()
        
        # Priority breakdown
        stats['by_priority'] = {
            'urgent': queryset.filter(priority='urgent').count(),
            'high': queryset.filter(priority='high').count(),
            'medium': queryset.filter(priority='medium').count(),
            'low': queryset.filter(priority='low').count(),
        }
        
        return Response(stats, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def consultancy_list(self, request):
        """Get list of active consultancies for assignment"""
        if request.user.role not in ['admin', 'hr_manager']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        consultancies = User.objects.filter(
            role='consultancy',
            is_active=True,
            company=request.user.company
        ).values('id', 'full_name', 'email', 'phone')
        
        return Response(list(consultancies), status=status.HTTP_200_OK)
    
    def _create_consultancy_link(self, job, consultancy_user):
        """
        Auto-create JobApplicationLink for consultancy assignment.
        If already exists and active, do nothing.
        """

        # Avoid duplicate active link for same consultancy & job
        existing_link = JobApplicationLink.objects.filter(
            job=job,
            created_by=consultancy_user,
            is_active=True
        ).first()

        if existing_link:
            return existing_link

        return JobApplicationLink.objects.create(
            job=job,
            created_by=consultancy_user,
            title=consultancy_user.name,
            platform="consultancy",   # adjust if you have choices
            is_active=True,
            expires_at=timezone.now() + timedelta(days=60)
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanAssignToConsultancy])
    def assign(self, request, pk=None):
        job = self.get_object()
        serializer = AssignJobSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        consultancy_ids = serializer.validated_data.get('consultancy_ids', [])
        internal_hr_ids = serializer.validated_data.get('internal_hr_ids', [])
        notes = serializer.validated_data.get('notes', '') or ''

        consultancies = User.objects.filter(id__in=consultancy_ids)
        internal_hrs = User.objects.filter(id__in=internal_hr_ids)

        now = timezone.now()

        # ✅ Assign consultancies
        if consultancies.exists():
            job.assigned_consultancies.add(*consultancies)

            if not job.assigned_to_consultancy:
                job.assigned_to_consultancy = consultancies.first()

            job.assigned_at = now
            job.assigned_by = request.user
            job.visible_to_consultancy = True

            for consultancy in consultancies:
                JobAssignmentHistory.objects.create(
                    job=job,
                    action='assigned',
                    consultancy=consultancy,
                    performed_by=request.user,
                    notes=notes
                )
                self._create_consultancy_link(job, consultancy)
                send_job_assignment_email(consultancy, job, request.user)

        # ✅ Assign internal HR
        if internal_hrs.exists():
            job.assigned_internal_hrs.add(*internal_hrs)

            if not job.assigned_to_internal_hr:
                job.assigned_to_internal_hr = internal_hrs.first()

            job.assigned_internal_at = now
            job.assigned_internal_by = request.user

            for hr in internal_hrs:
                JobAssignmentHistory.objects.create(
                    job=job,
                    action='assigned_internal',
                    consultancy=hr,
                    performed_by=request.user,
                    notes=notes
                )
                send_job_assignment_email(hr, job, request.user)

        # ✅ Status logic (VERY IMPORTANT)
        if job.assigned_consultancies.exists() and job.assigned_internal_hrs.exists():
            job.status = 'assigned_to_both'
        elif job.assigned_consultancies.exists():
            job.status = 'assigned_to_consultancy'
        elif job.assigned_internal_hrs.exists():
            job.status = 'assigned_to_internal_hr'

        job.save()

        return Response({
            'message': 'Job assigned successfully',
            'data': JobDetailSerializer(job, context={'request': request}).data
        }, status=status.HTTP_200_OK)

class JobApplicationLinkViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Job Application Links"""
    
    queryset = JobApplicationLink.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return JobApplicationLinkCreateSerializer
        return JobApplicationLinkSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = JobApplicationLink.objects.select_related('job', 'created_by')
        
        # Filter based on user role
        if user.role in ['admin', 'hr_manager']:
            # Can see all links
            pass
        elif user.role == 'hr':
            # Internal HR: only links for jobs assigned to them (or created by them if you prefer)
            queryset = queryset.filter(job__assigned_to_internal_hr=user)
        elif user.role == 'consultancy':
            # Can only see links for jobs assigned to them
            queryset = queryset.filter(created_by=user)
        else:
            queryset = queryset.none()
        
        # Apply filters
        job_filter = self.request.query_params.get('job')
        if job_filter and is_valid_uuid(job_filter):
            queryset = queryset.filter(job_id=job_filter)
        
        platform_filter = self.request.query_params.get('platform')
        if platform_filter:
            queryset = queryset.filter(platform=platform_filter)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        if hasattr(user, 'company'):
            queryset = queryset.filter(job__company=user.company)
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle link active status"""
        link = self.get_object()
        link.is_active = not link.is_active
        link.save()
        
        serializer = JobApplicationLinkSerializer(link, context={'request': request})
        return Response({
            'message': f'Link {"activated" if link.is_active else "deactivated"} successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def track_view(self, request, pk=None):
        """Track link view (public endpoint)"""
        link = self.get_object()
        
        if link.is_expired():
            return Response(
                {'error': 'This link has expired'},
                status=status.HTTP_410_GONE
            )
        
        if not link.is_active:
            return Response(
                {'error': 'This link is no longer active'},
                status=status.HTTP_410_GONE
            )
        
        # Increment views
        link.increment_views()
        
        # Return job details for application form
        return Response({
            'job_title': link.job.job_title,
            'department': link.job.department.name if link.job.department else None,
            'location': link.job.location,
            'experience_range': link.job.experience_range,
            'skills_competencies': link.job.skills_competencies,
            'job_description': link.job.job_description,
            'application_token': link.unique_token,
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get link statistics"""
        user = request.user
        
        if user.role in ['admin', 'hr_manager', 'hr']:
            queryset = JobApplicationLink.objects.all()
        elif user.role == 'consultancy':
            queryset = JobApplicationLink.objects.filter(job__assigned_to_consultancy=user)
        else:
            queryset = JobApplicationLink.objects.none()
        
        from django.db.models import Sum
        stats = {
            'total_links': queryset.count(),
            'active_links': queryset.filter(is_active=True).count(),
            'total_views': queryset.aggregate(total=Sum('views_count'))['total'] or 0,
            'total_applications': queryset.aggregate(total=Sum('applications_count'))['total'] or 0,
            'by_platform': {}
        }
        
        # Platform-wise breakdown
        platforms = queryset.values('platform').annotate(
            count=Count('id'),
            views=Sum('views_count'),
            applications=Sum('applications_count')
        )
        
        for platform in platforms:
            stats['by_platform'][platform['platform']] = {
                'links': platform['count'],
                'views': platform['views'] or 0,
                'applications': platform['applications'] or 0
            }
        
        return Response(stats, status=status.HTTP_200_OK)

from rest_framework.pagination import PageNumberPagination

class JobApplicationPagination(PageNumberPagination):
    page_size = 500

class JobApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Job Applications"""
    
    queryset = JobApplication.objects.all()
    
    filter_backends = [DjangoFilterBackend]
    filterset_class = JobApplicationFilter

    def get_pagination_class(self):
        if self.action == 'list':
            return JobApplicationPagination
        return super().get_pagination_class()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return JobApplicationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return JobApplicationUpdateSerializer
        elif self.action == 'public_apply':
            return PublicJobApplicationCreateSerializer
        return JobApplicationSerializer
    
    def get_permissions(self):
        # 🔓 Public GET access
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]

        if self.action == 'public_apply':
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated(), CanSubmitApplications()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageApplications()]

        return [IsAuthenticated(), CanViewApplications()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = JobApplication.objects.select_related(
            'job', 'job__department', 'submitted_by', 'application_link'
        )
        if not user.is_authenticated:
            return queryset.order_by(
                F('match_score').desc(nulls_last=True),
                '-created_at'
            )
        # Filter based on user role
        if user.role in ['admin', 'hr_manager']:
            # Can see all applications
            pass
        elif user.role == 'hr':
            # Internal HR: only applications for jobs assigned to them
            queryset = queryset.filter(job__assigned_to_internal_hr=user)
        elif user.role == 'consultancy':
            # Can see applications for jobs assigned to them
            queryset = queryset.filter(job__assigned_to_consultancy=user,source='consultancy')
        else:
            queryset = queryset.none()
        # Apply filters
        job_filter = self.request.query_params.get('job')
        if job_filter and is_valid_uuid(job_filter):
            queryset = queryset.filter(job_id=job_filter)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        source_filter = self.request.query_params.get('source')
        if source_filter:
            queryset = queryset.filter(source=source_filter)
        
        platform_filter = self.request.query_params.get('platform')
        if platform_filter:
            queryset = queryset.filter(application_link__platform=platform_filter)
        
        my_applications = self.request.query_params.get('my_applications')
        if my_applications and my_applications.lower() == 'true':
            queryset = queryset.filter(submitted_by=user)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(candidate_name__icontains=search) |
                Q(candidate_email__icontains=search) |
                Q(candidate_phone__icontains=search)
            )
        queryset = queryset.order_by(F('match_score').desc(nulls_last=True), '-created_at')
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def public_apply(self, request):
        """
        Public endpoint for direct resume upload - NO FORM REQUIRED
        Candidate just uploads resume file with application token
        """
        serializer = PublicJobApplicationCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        applications = serializer.save()
        
        return Response({
            'success': True,
            'message': f'{len(applications)} resume(s) uploaded successfully',
            'applications': [
                {
                    'application_id': str(app.id),
                    'job_title': app.job.job_title,
                    'status': app.status
                }
                for app in applications
            ]
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get application statistics"""
        user = request.user
        
        if user.role in ['admin', 'hr_manager', 'hr']:
            queryset = JobApplication.objects.all()
        elif user.role == 'consultancy':
            queryset = JobApplication.objects.filter(job__assigned_to_consultancy=user)
        else:
            queryset = JobApplication.objects.none()
        
        stats = {
            'total': queryset.count(),
            'received': queryset.filter(status='received').count(),
            # 'screening': queryset.filter(status='screening').count(),
            'shortlisted': queryset.filter(status='shortlisted').count(),
            # 'interviewed': queryset.filter(status='interviewed').count(),
            'selected': queryset.filter(status='selected').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'joined': queryset.filter(status='joined').count(),
        }
        
        # Source breakdown
        stats['by_source'] = {
            'internal_hr': queryset.filter(source='internal_hr').count(),
            'consultancy': queryset.filter(source='consultancy').count(),
            'application_link': queryset.filter(source='application_link').count(),
            # 'direct': queryset.filter(source='direct').count(),
            'referral': queryset.filter(source='referral').count(),
        }
        
        return Response(stats, status=status.HTTP_200_OK)
    
class ReferralApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Referral Applications"""
    
    queryset = ReferralApplication.objects.all()
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action == 'create':
            return ReferralApplicationCreateSerializer
        return ReferralApplicationSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Override create to return read serializer response
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        applications = serializer.save()

        # Return full response using read serializer
        response_serializer = ReferralApplicationSerializer(
            applications,many=True,
            context={'request': request}
        )
        return Response(
            {
                "success": True,
                "count": len(applications),
                "applications": response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'])
    def create_job_application_from_referral(self, request, *args, **kwargs):
        """
        Custom action to create a JobApplication from an existing ReferralApplication.
        Requires referral_application_id and job_id in the request.
        """
        # Use the ReferralToJobApplicationCreateSerializer
        serializer = ReferralToJobApplicationCreateSerializer(data=request.data)

        if serializer.is_valid():
            job_application = serializer.save()
            return Response(
                {
                    "message": "Job application created successfully",
                    "job_application_id": str(job_application.id)
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
from .serializers import (
    CareersJobListSerializer,
    CareersJobDetailSerializer,
    CareersApplicationCreateSerializer
)
from django.shortcuts import get_object_or_404

class CareersViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Career Page APIs
    - List active jobs
    - Retrieve job detail
    - Apply for a job (resume upload)
    """
    queryset = Job.objects.filter(is_active=True)
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return CareersJobListSerializer
        elif self.action == 'retrieve':
            return CareersJobDetailSerializer
        elif self.action == 'apply':
            return CareersApplicationCreateSerializer
        return CareersJobListSerializer

    # GET /api/careers/
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        department_filter = self.request.query_params.get('department')
        if department_filter and department_filter == 'other':
            queryset = queryset.filter(department__name__in=['HR and Administration','Internal Accounts','IT','Marketing'])
        else:
            if department_filter and department_filter != '' and is_valid_uuid(department_filter):
                queryset = queryset.filter(department_id=department_filter)

        designation_filter = self.request.query_params.get('designation')
        if designation_filter and designation_filter != '' and is_valid_uuid(designation_filter):
            queryset = queryset.filter(designation_id=designation_filter)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # GET /api/careers/{id}/
    def retrieve(self, request, pk=None):
        job = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(job)
        return Response(serializer.data)

    # POST /api/careers/apply/
    @action(detail=False, methods=['post'], url_path='apply')
    def apply(self, request):
        """
        Apply to a job by uploading one or multiple resumes.
        Required:
            - job_id
            - resumes (list of files)
        """
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        applications = serializer.save()

        return Response(
            {
                "message": "Application(s) submitted successfully.",
                "applications_created": len(applications)
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'])
    def create_job_application_from_career(self, request, *args, **kwargs):
        """
        Custom action to create a JobApplication from an existing Application.
        Requires application_id and job_id in the request.
        """
        # Use the ReferralToJobApplicationCreateSerializer
        serializer = CareerToJobApplicationCreateSerializer(data=request.data)

        if serializer.is_valid():
            job_application = serializer.save()
            return Response(
                {
                    "message": "Job application created successfully",
                    "job_application_id": str(job_application.id)
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='applications')
    def applications(self, request):
        """
        List all resumes uploaded from Careers page
        """
        queryset = Application.objects.filter(source='career_page').order_by('-created_at')

        serializer = ApplicationSerializer(
            queryset,
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)

class JobDropDownListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API to get job dropdown (no pagination)
    """
    serializer_class = JobDropDownListSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        queryset = Job.objects.select_related(
            'department',
            'designation',
            'posted_by'
        ).only(
            'id',
            'job_title',
            'department__name',
            'designation__name',
            'posted_by__name',
            'company',
            'is_active'
        )

        if not user.is_authenticated:
            return queryset.filter(is_active=True)
        
        # Filter based on user role
        if user.role in ['admin', 'hr_manager']:
            # Can see all jobs
            pass
        elif user.role == 'department_head':
            # Can see jobs from their department
            if hasattr(user, 'headed_department'):
                queryset = queryset.filter(department=user.headed_department)
            else:
                queryset = queryset.none()
        elif user.role == 'hr':
            # Internal HR: only jobs assigned to them OR jobs they posted
            queryset = queryset.filter(
                Q(assigned_to_internal_hr=user) | Q(posted_by=user) | Q(assigned_internal_hrs=user)
            )
        elif user.role == 'consultancy':
            # Can see assigned jobs or publicly visible jobs
            queryset = queryset.filter(
                Q(assigned_to_consultancy=user) | Q(visible_to_consultancy=True) | Q(assigned_consultancies=user)
            )
        else:
            queryset = queryset.none()
        
        if hasattr(user, 'company'):
            queryset = queryset.filter(company=user.company)
        
        return queryset.filter(is_active=True).order_by('job_title')
    
class ApplicationViewSet(viewsets.GenericViewSet):
    queryset = Job.objects.filter(is_active=True)
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'apply':
            return ApplicationCreateSerializer
        elif self.action == 'convert':
            return ApplicationToJobSerializer
        return CareersJobListSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = CareersJobListSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        job = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = CareersJobDetailSerializer(job)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def apply(self, request):
        """
        POST /apply/
        body:
        {
            "job_id": "...",
            "source": "linkedin",
            "resumes": [...]
        }
        """
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        apps = serializer.save()

        return Response({
            "message": "Applications submitted",
            "count": len(apps)
        })

    @action(detail=False, methods=['post'])
    def convert(self, request):
        """
        Convert Application → JobApplication
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job_app = serializer.save()

        return Response({
            "message": "Converted successfully",
            "job_application_id": str(job_app.id)
        })

    @action(detail=False, methods=['get'])
    def applications(self, request):
        source = request.query_params.get('source')

        queryset = Application.objects.all()

        if source:
            queryset = queryset.filter(source=source)

        serializer = ApplicationSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)