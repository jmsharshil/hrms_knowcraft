from rest_framework import serializers
from .models import Job, JobAssignmentHistory, JobApplication, JobApplicationLink
from accounts.models import User
from django.db import IntegrityError, transaction

class JobListSerializer(serializers.ModelSerializer):
    """Serializer for job list view"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    assigned_to_name = serializers.CharField(
        source='assigned_to_consultancy.name',
        read_only=True,
        allow_null=True
    )
    assigned_internal_name = serializers.CharField(
        source='assigned_to_internal_hr.name',
        read_only=True,
        allow_null=True
    )
    mrf_requisition_no = serializers.CharField(source='mrf.requisition_no', read_only=True)
    applications_count = serializers.SerializerMethodField()
    remaining_positions = serializers.SerializerMethodField()
    job_type_display = serializers.CharField(source='get_job_type_display', read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'job_title', 'department', 'department_name',
            'designation', 'designation_name', 'location','job_type', 'job_type_display',
            'no_of_positions', 'positions_filled', 'remaining_positions',
            'status', 'status_display', 'priority', 'priority_display',
            'assigned_to_consultancy', 'assigned_to_name',
            'assigned_to_internal_hr', 'assigned_internal_name',
            'expected_closure_date', 'created_at', 'mrf_requisition_no',
            'applications_count', 'is_active', 'visible_to_consultancy'
        ]
    
    def get_applications_count(self, obj):
        return obj.applications.count()
    
    def get_remaining_positions(self, obj):
        return obj.remaining_positions()


class JobDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed job view"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    assigned_to_name = serializers.CharField(
        source='assigned_to_consultancy.name',
        read_only=True,
        allow_null=True
    )
    assigned_to_email = serializers.CharField(
        source='assigned_to_consultancy.email',
        read_only=True,
        allow_null=True
    )
    assigned_by_name = serializers.CharField(
        source='assigned_by.name',
        read_only=True,
        allow_null=True
    )
    
    # NEW: internal HR fields
    assigned_internal_name = serializers.CharField(
        source='assigned_to_internal_hr.name',
        read_only=True,
        allow_null=True
    )
    assigned_internal_email = serializers.CharField(
        source='assigned_to_internal_hr.email',
        read_only=True,
        allow_null=True
    )
    assigned_internal_by_name = serializers.CharField(
        source='assigned_internal_by.name',
        read_only=True,
        allow_null=True
    )
    
    posted_by_name = serializers.CharField(
        source='posted_by.name',
        read_only=True,
        allow_null=True
    )
    
    mrf_details = serializers.SerializerMethodField()
    applications_summary = serializers.SerializerMethodField()
    application_links_count = serializers.SerializerMethodField()
    remaining_positions = serializers.SerializerMethodField()
    job_type_display = serializers.CharField(source='get_job_type_display', read_only=True)
    class Meta:
        model = Job
        fields = '__all__'
    
    def get_mrf_details(self, obj):
        return {
            'id': str(obj.mrf.id),
            'requisition_no': obj.mrf.requisition_no,
            'mrf_name': obj.mrf.mrf_name,
            'requested_by': obj.mrf.requested_by_name,
            'approved_at': obj.mrf.approved_at,
        }
    
    def get_applications_summary(self, obj):
        return {
            'total': obj.applications.count(),
            'received': obj.applications.filter(status='received').count(),
            'screening': obj.applications.filter(status='screening').count(),
            'shortlisted': obj.applications.filter(status='shortlisted').count(),
            'interviewed': obj.applications.filter(status='interviewed').count(),
            'selected': obj.applications.filter(status='selected').count(),
            'rejected': obj.applications.filter(status='rejected').count(),
        }
    
    def get_application_links_count(self, obj):
        return obj.application_links.filter(is_active=True).count()
    
    def get_remaining_positions(self, obj):
        return obj.remaining_positions()


class JobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating jobs from MRF"""
    
    class Meta:
        model = Job
        fields = [
            'mrf', 'priority', 'expected_closure_date',
            'visible_to_consultancy', 'job_description'
        ]
    
    def validate_mrf(self, value):
        if value.status != 'approved':
            raise serializers.ValidationError(
                "Job can only be created from approved MRF"
            )
        
        if hasattr(value, 'job'):
            raise serializers.ValidationError(
                "Job already exists for this MRF"
            )
        
        return value
    
    def create(self, validated_data):
        mrf = validated_data['mrf']
        user = self.context['request'].user
        
        job = Job.objects.create(
            mrf=mrf,
            job_title=mrf.mrf_name,
            department=mrf.department,
            designation=mrf.designation,
            location=mrf.location,
            job_type=mrf.job_type,
            no_of_positions=mrf.no_of_vacancies,
            key_responsibility=mrf.key_responsibility,
            required_qualifications=mrf.required_qualifications,
            experience_range=mrf.experience_range,
            skills_competencies=mrf.skills_competencies,
            salary_range=mrf.salary_range,
            priority=validated_data.get('priority', 'medium'),
            expected_closure_date=validated_data.get('expected_closure_date'),
            visible_to_consultancy=validated_data.get('visible_to_consultancy', False),
            job_description=validated_data.get('job_description', ''),
            posted_by=user,
            company=user.company,
            status='open'
        )
        
        # Create history record
        JobAssignmentHistory.objects.create(
            job=job,
            action='created',
            performed_by=user,
            notes='Job created from approved MRF'
        )
        
        return job


class JobUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating job details - NOW INCLUDES PRIORITY"""
    
    class Meta:
        model = Job
        fields = [
            'priority', 'expected_closure_date', 'status','job_type',
            'is_active', 'visible_to_consultancy', 'job_description'
        ]
    
    def update(self, instance, validated_data):
        # Track priority change
        if 'priority' in validated_data and instance.priority != validated_data['priority']:
            old_priority = instance.priority
            new_priority = validated_data['priority']
            
            instance = super().update(instance, validated_data)
            
            # Create history record for priority change
            JobAssignmentHistory.objects.create(
                job=instance,
                action='priority_changed',
                performed_by=self.context['request'].user,
                old_value=old_priority,
                new_value=new_priority,
                notes=f'Priority changed from {old_priority} to {new_priority}'
            )
        else:
            instance = super().update(instance, validated_data)
        
        return instance


class AssignToConsultancySerializer(serializers.Serializer):
    """Serializer for assigning job to consultancy"""
    
    consultancy_id = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_consultancy_id(self, value):
        try:
            user = User.objects.get(id=value, role='consultancy', is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid consultancy user")
        return value

class AssignToBothSerializer(serializers.Serializer):
    consultancy_id = serializers.UUIDField()
    internal_hr_id = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class CloseJobSerializer(serializers.Serializer):
    """Serializer for closing a job"""
    
    closure_notes = serializers.CharField(required=False, allow_blank=True)


# ============= APPLICATION LINK SERIALIZERS =============

class JobApplicationLinkSerializer(serializers.ModelSerializer):
    """Serializer for job application links"""
    
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    application_url = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(
        source='created_by.name',
        read_only=True,
        allow_null=True
    )
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = JobApplicationLink
        fields = [
            'id', 'job', 'job_title', 'platform', 'platform_display',
            'platform_name', 'title', 'description', 'unique_token',
            'application_url', 'views_count', 'applications_count',
            'is_active', 'expires_at', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'is_expired'
        ]
        read_only_fields = ['unique_token', 'views_count', 'applications_count']
    
    def get_application_url(self, obj):
        return obj.get_application_url()
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class JobApplicationLinkCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating application links"""
    
    class Meta:
        model = JobApplicationLink
        fields = [
            'job', 'platform', 'platform_name', 'title',
            'description', 'expires_at'
        ]
    
    def validate_job(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot create link for inactive job")
        
        if value.status not in ['open', 'assigned_to_consultancy', 'assigned_to_internal_hr','in_progress','assigned_to_both']:
            raise serializers.ValidationError("Job is not accepting applications")
        
        return value
    
    def validate(self, data):
        # If platform is 'other', platform_name is required
        if data.get('platform') == 'other' and not data.get('platform_name'):
            raise serializers.ValidationError({
                'platform_name': 'Platform name is required when platform is "other"'
            })
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        link = JobApplicationLink.objects.create(
            **validated_data,
            created_by=user
        )
        
        return link


# ============= APPLICATION SERIALIZERS =============

class JobApplicationSerializer(serializers.ModelSerializer):
    """Serializer for job applications"""
    
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    department_name = serializers.CharField(source='job.department.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    submitted_by_name = serializers.CharField(
        source='submitted_by.name',
        read_only=True,
        allow_null=True
    )
    platform_name = serializers.SerializerMethodField()
    resume_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'job_title', 'department_name', 'candidate_name',
            'candidate_email', 'candidate_phone', 'resume', 'resume_url',
            'original_filename', 'file_size', 'file_size_mb', 'cover_letter',
            'experience_years','relevant_experience_years', 'current_ctc', 'expected_ctc', 'notice_period',
            'linkedin_url', 'portfolio_url','skill','education','location','current_employer','match_score', 'status', 'status_display',
            'source', 'source_display', 'platform_name', 'application_link','is_duplicate',
            'submitted_by', 'submitted_by_name', 'notes', 'rating','resume_report',
            'created_at', 'updated_at'
        ]
    
    def get_platform_name(self, obj):
        return obj.get_platform_name()
    
    def get_resume_url(self, obj):
        if obj.resume:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.resume.url)
            return obj.resume.url
        return None
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0


class JobApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating job applications"""
    
    class Meta:
        model = JobApplication
        fields = [
            'job', 'candidate_name', 'candidate_email', 'candidate_phone',
            'resume', 'cover_letter', 'experience_years', 'current_ctc',
            'expected_ctc', 'notice_period', 'linkedin_url', 'portfolio_url'
        ]
    
    def validate_job(self, value):
        if not value.is_active:
            raise serializers.ValidationError("This job is no longer active")
        
        if value.status not in ['open', 'assigned_to_consultancy', 'in_progress','assigned_to_both']:
            raise serializers.ValidationError("This job is not accepting applications")
        
        return value
    
    def validate_resume(self, value):
        if value:
            # Validate file size (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Resume file size must be less than 5MB")
            
            # Validate file extension
            allowed_extensions = ['.pdf', '.doc', '.docx']
            import os
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Only {', '.join(allowed_extensions)} files are allowed"
                )
        
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Determine source based on user role
        if user.role == 'consultancy':
            source = 'consultancy'
        elif user.role in ['hr', 'hr_manager', 'admin']:
            source = 'internal_hr'
        else:
            source = 'direct'
        
        application = JobApplication.objects.create(
            **validated_data,
            submitted_by=user,
            source=source,
            status='received'
        )
        
        return application


class PublicJobApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for direct resume upload through links - NO FORM REQUIRED"""

    application_token = serializers.CharField(write_only=True)
    resume = serializers.FileField(required=True)

    class Meta:
        model = JobApplication
        fields = ['application_token', 'resume']

    def validate_application_token(self, value):
        try:
            link = JobApplicationLink.objects.get(unique_token=value, is_active=True)

            # Check if link is expired
            if link.is_expired():
                raise serializers.ValidationError("This application link has expired")

            # Check if job is still accepting applications
            if not link.job.is_active:
                raise serializers.ValidationError("This job is no longer active")

            allowed_statuses = [
                'open',
                'assigned_to_consultancy',
                'assigned_to_both',
            ]

            if link.job.status not in allowed_statuses:
                # relax check if the link was created by an internal HR user
                creator = getattr(link, 'created_by', None)
                if not (creator and getattr(creator, 'role', None) in ['hr', 'hr_manager']):
                    raise serializers.ValidationError("This job is not accepting applications")

            self.context['application_link'] = link

        except JobApplicationLink.DoesNotExist:
            raise serializers.ValidationError("Invalid application link")

        return value

    def validate_resume(self, value):
        if not value:
            raise serializers.ValidationError("Resume file is required")

        # Validate file size (max 10MB for any format)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError("File size must be less than 10MB")

        # Allow all common document and image formats
        allowed_extensions = [
            '.pdf', '.doc', '.docx', '.txt', '.rtf',  # Documents
            '.jpg', '.jpeg', '.png', '.gif',  # Images
            '.odt', '.pages',  # Other formats
        ]

        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"File format not supported. Allowed formats: {', '.join(allowed_extensions)}"
            )

        return value

    def create(self, validated_data):
        # remove token from payload
        validated_data.pop('application_token', None)
        link = self.context['application_link']
        request = self.context.get('request')

        resume_file = validated_data['resume']
        
        # prepare values to save
        original_filename = getattr(resume_file, 'name', '')
        file_size = getattr(resume_file, 'size', 0)

        try:
            with transaction.atomic():
                application = JobApplication.objects.create(
                    job=link.job,
                    resume=resume_file,
                    application_link=link,
                    source='application_link',
                    status='received',
                    original_filename=original_filename,
                    file_size=file_size,
                    # submitted_by remains null for public uploads
                    # candidate_email intentionally left null to avoid duplicate empty-string constraint
                )

                # Increment link statistics AFTER successful create
                link.increment_applications()

        except IntegrityError as e:
            # Convert DB integrity error to serializer validation error so API returns 400
            raise serializers.ValidationError({
                'non_field_errors': [
                    'Could not create application. Possible duplicate candidate entry for this job.'
                ]
            })
        from onboarding.utils.task_queue import TASK_QUEUE
        from .utils import parse_resume_task
        TASK_QUEUE.enqueue(parse_resume_task,application,application.resume.file,link.job)
        return application


class JobApplicationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating job application"""
    
    class Meta:
        model = JobApplication
        fields = ['status', 'notes', 'rating']
    
    def validate_status(self, value):
        instance = self.instance
        current_status = instance.status
        
        # Define allowed status transitions
        # allowed_transitions = {
        #     'received': ['screening', 'rejected', 'withdrawn'],
        #     'screening': ['shortlisted', 'rejected'],
        #     'shortlisted': ['interview_scheduled', 'rejected'],
        #     'interview_scheduled': ['interviewed', 'rejected'],
        #     'interviewed': ['selected', 'rejected'],
        #     'selected': ['offer_sent', 'rejected'],
        #     'offer_sent': ['offer_accepted', 'offer_declined'],
        #     'offer_accepted': ['joined'],
        # }
        from onboarding.utils.stage_transition_rules import validate_transition
        ok,reason = validate_transition(current_status,value)
        if ok:
            return value
        else:
            raise serializers.ValidationError(reason)

        # if current_status in allowed_transitions:
        #     if value not in allowed_transitions[current_status] and value != current_status:
        #         raise serializers.ValidationError(
        #             f"Cannot change status from {current_status} to {value}"
        #         )
        
        # return value


class JobAssignmentHistorySerializer(serializers.ModelSerializer):
    """Serializer for job history"""
    
    consultancy_name = serializers.CharField(
        source='consultancy.name',
        read_only=True,
        allow_null=True
    )
    performed_by_name = serializers.CharField(
        source='performed_by.name',
        read_only=True,
        allow_null=True
    )
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = JobAssignmentHistory
        fields = '__all__'
        
class AssignToInternalHRSerializer(serializers.Serializer):
    """Serializer for assigning job to internal HR"""
    internal_hr_id = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_internal_hr_id(self, value):
        try:
            user = User.objects.get(id=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid internal HR user")

        # Accept hr or hr_manager roles — adjust to your roles if needed
        if user.role not in ['hr', 'hr_manager']:
            raise serializers.ValidationError("User is not an internal HR")
        return value
