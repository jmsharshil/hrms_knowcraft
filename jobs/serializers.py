from mrf.serializers import MRFListSerializer
from rest_framework import serializers
from .models import Job, JobAssignmentHistory, JobApplication, JobApplicationLink,ReferralApplication,Application,ApplicationSource
from accounts.models import User
from django.db import IntegrityError, transaction

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
            'created_at', 'updated_at', 'is_expired','qr_code'
        ]
        read_only_fields = ['unique_token', 'views_count', 'applications_count','qr_code']
    
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

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email']

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
    assigned_consultancies_details = SimpleUserSerializer(
        source='assigned_consultancies',
        many=True,
        read_only=True
    )

    assigned_internal_hrs_details = SimpleUserSerializer(
        source='assigned_internal_hrs',
        many=True,
        read_only=True
    )
    application_links = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'job_title', 'department', 'department_name','is_private',
            'designation', 'designation_name', 'location','job_type', 'job_type_display',
            'no_of_positions', 'positions_filled', 'remaining_positions',
            'status', 'status_display', 'priority', 'priority_display',
            'assigned_to_consultancy', 'assigned_to_name',
            'assigned_to_internal_hr', 'assigned_internal_name',
            'expected_closure_date', 'created_at', 'mrf_requisition_no',
            'applications_count', 'is_active', 'visible_to_consultancy',
            'assigned_consultancies_details','assigned_internal_hrs_details','application_links'
        ]
    
    def get_application_links(self, obj):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return []

        user = request.user
        if user.role== 'consultancy':
            links = obj.application_links.filter(created_by=user) if hasattr(obj, 'application_links') else obj.jobapplicationlink_set.filter(created_by=user)
        else:
            links = obj.application_links.all()

        return JobApplicationLinkSerializer(
            links,
            many=True,
            context=self.context
        ).data
    
    def get_applications_count(self, obj):
        return obj.applications.count()
    
    def get_remaining_positions(self, obj):
        return obj.remaining_positions()

# ============= APPLICATION SERIALIZERS =============

class JobApplicationMiniSerializer(serializers.ModelSerializer):
    """Serializer for job applications"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    submitted_by_name = serializers.CharField(
        source='submitted_by.name',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'candidate_name','candidate_email', 'candidate_phone',
            'status_display','source_display', 'submitted_by_name','joining_date',
            'created_at','updated_at'
        ]
    
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
    joining_applications = serializers.SerializerMethodField()
    application_links_count = serializers.SerializerMethodField()
    remaining_positions = serializers.SerializerMethodField()
    job_type_display = serializers.CharField(source='get_job_type_display', read_only=True)

    assigned_consultancies_details = SimpleUserSerializer(
        source='assigned_consultancies',
        many=True,
        read_only=True
    )

    assigned_internal_hrs_details = SimpleUserSerializer(
        source='assigned_internal_hrs',
        many=True,
        read_only=True
    )

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
            'shortlisted': obj.applications.filter(status='shortlisted').count(),
            'interview_pending': obj.applications.filter(status__in=('interview_pending_1','interview_pending_2','interview_pending_3','interview_pending_final','interview_pending_management_client')).count(),
            "shortlisted_for_next_round": obj.applications.filter(status__in=('interview_next_2','interview_next_3','interview_next_final','interview_next_management_client')).count(),
            'selected': obj.applications.filter(status='selected').count(),
            'joining_pending': obj.applications.filter(status='joining_pending').count(),
            'joined': obj.applications.filter(status='joined').count(),
            'rejected': obj.applications.filter(status__in=('rejected','interview_rejected_1','interview_rejected_2','interview_rejected_3','interview_rejected_final','interview_rejected_management_client','rejected_after_final_round')).count(),
        }
    
    def get_joining_applications(self, obj):
        apps = obj.applications.filter(status__in=['joining_pending', 'joined'])
        return JobApplicationMiniSerializer(apps, many=True, context=self.context).data
    
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
            status='open',
            is_private=mrf.is_private,  # Inherit privacy from MRF
        )
        
        # Inherit selected_viewers from private MRF
        if mrf.is_private:
            viewers = mrf.selected_viewers.all()
            if viewers.exists():
                job.selected_viewers.set(viewers)
        
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
    
    # consultancy_id = serializers.UUIDField()
    consultancy_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_consultancy_ids(self, value):
        users = User.objects.filter(id__in=value, role='consultancy', is_active=True, company=self.context['request'].user.company)
        
        if len(users) != len(value):
            raise serializers.ValidationError("One or more consultancy users are invalid")
        
        return value

class AssignToBothSerializer(serializers.Serializer):
    consultancy_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    internal_hr_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        if not data.get('consultancy_ids') and not data.get('internal_hr_ids'):
            raise serializers.ValidationError("At least one assignment is required")
        return data

class CloseJobSerializer(serializers.Serializer):
    """Serializer for closing a job"""
    
    closure_notes = serializers.CharField(required=False, allow_blank=True)

# ============= APPLICATION SERIALIZERS =============

class JobApplicationSerializer(serializers.ModelSerializer):
    """Serializer for job applications"""
    
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    department_name = serializers.CharField(source='job.department.name', read_only=True)
    designation_name = serializers.CharField(source='job.designation.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    round_name_display = serializers.CharField(source='get_round_name_display', read_only=True)
    submitted_by_name = serializers.CharField(
        source='submitted_by.name',
        read_only=True,
        allow_null=True
    )
    uploaded_by_name = serializers.CharField(
        source='application_link.created_by.name',
        read_only=True,
        allow_null=True
    )
    uploaded_by_email = serializers.CharField(
        source='application_link.created_by.email',
        read_only=True,
        allow_null=True
    )
    uploaded_by_role = serializers.CharField(
        source='application_link.created_by.role',
        read_only=True,
        allow_null=True
    )
    uploaded_by_phone = serializers.CharField(
        source='application_link.created_by.phone',
        read_only=True,
        allow_null=True
    )
    platform_name = serializers.SerializerMethodField()
    resume_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    document_upload_link = serializers.SerializerMethodField()
    candidate_experience_link = serializers.SerializerMethodField()
    is_private = serializers.SerializerMethodField()
    mrf_details = serializers.SerializerMethodField()
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'job_title', 'department_name', 'candidate_name','designation_name',
            'candidate_email', 'candidate_phone', 'resume', 'resume_url',
            'original_filename', 'file_size', 'file_size_mb', 'cover_letter',"rejection_reason",
            'experience_years','relevant_experience_years', 'current_ctc', 'expected_ctc', 'notice_period',
            'linkedin_url', 'portfolio_url','skill','education','location','current_employer','match_score', 'status', 'status_display',
            'source', 'source_display', 'platform_name', 'application_link','is_duplicate',"referral_name","referral_email","referral_phone",
            "referral_emp_code","referral_designation","referral_department","is_shortlisted","consolidated_feedback_avg",
            'submitted_by', 'submitted_by_name', 'notes', 'rating','resume_report','slot_link','candidate_history',
            'created_at', 'updated_at','is_selected','is_approved','is_rejected','inperson_link','reschedule_count','no_show_count',
            'interview_scheduled_at','interviewer_name','interview_link','feedback_link','round_name','round_name_display',
            "uploaded_by_name","uploaded_by_email","uploaded_by_role","uploaded_by_phone","interview_end_at",
            "document_upload_link", "candidate_experience_link","is_private","mrf_details"
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

    def get_document_upload_link(self, obj):
        from django.conf import settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net')
        return f"{frontend_url}/api/application/documents/upload/{obj.id}"

    def get_candidate_experience_link(self, obj):
        from django.conf import settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net')
        return f"{frontend_url}/candidate/feedback/{obj.id}"

    def get_is_private(self, obj):
        return obj.job.is_private

    def get_mrf_details(self, obj):
        return MRFListSerializer(obj.job.mrf).data


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
        
        if value.status not in ['open', 'assigned_to_consultancy', 'in_progress','assigned_to_both', 'assigned_to_internal_hr']:
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
    # resume = serializers.FileField(required=True)
    resumes = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=True
    )

    class Meta:
        model = JobApplication
        fields = ['application_token', 'resumes']

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
                'assigned_to_internal_hr',
                'assigned_to_both',
            ]

            if link.job.status not in allowed_statuses:
                # relax check if the link was created by an internal HR user
                creator = getattr(link, 'created_by', None)
                if not (creator and getattr(creator, 'role', None) in ['hr', 'hr_manager', 'admin']):
                    raise serializers.ValidationError("This job is not accepting applications.")

            self.context['application_link'] = link

        except JobApplicationLink.DoesNotExist:
            raise serializers.ValidationError("Invalid application link")

        return value

    def validate_resumes(self, values):
        if not values:
            raise serializers.ValidationError("At least one resume file is required")

        for value in values:
            # Validate file size (max 10MB)
            max_size = 10 * 1024 * 1024
            if value.size > max_size:
                raise serializers.ValidationError(
                    f"{value.name}: File size must be less than 10MB"
                )

            allowed_extensions = [
                '.pdf', '.doc', '.docx', '.txt', '.rtf',
                '.jpg', '.jpeg', '.png', '.gif',
                '.odt', '.pages',
            ]

            import os
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"{value.name}: Unsupported file format"
                )

        return values

    def create(self, validated_data):
        validated_data.pop('application_token', None)
        resumes = validated_data.pop('resumes')

        link = self.context['application_link']
        request = self.context.get('request')
        created_applications = []

        try:
            with transaction.atomic():
                for resume_file in resumes:
                    application = JobApplication.objects.create(
                        job=link.job,
                        resume=resume_file,
                        application_link=link,
                        source='application_link',
                        status='received',
                        original_filename=getattr(resume_file, 'name', ''),
                        file_size=getattr(resume_file, 'size', 0),
                    )

                    # referral logic (unchanged)
                    data = request.data
                    if application.get_platform_name() in ["Employee Referral", "referral"]:
                        application.referral_name = data.get('referral_name', "")
                        application.referral_email = data.get("referral_email", "")
                        application.referral_phone = data.get("referral_phone", "")
                        application.referral_emp_code = data.get('referral_emp_code', "")
                        application.referral_department = data.get("referral_department", "")
                        application.referral_designation = data.get("referral_designation", "")
                        application.save()
                    
                    if application.get_platform_name() == 'Consultancy':
                        application.source = 'consultancy'
                        application.save()

                    link.increment_applications()
                    created_applications.append(application)

        except IntegrityError:
            raise serializers.ValidationError({
                'non_field_errors': [
                    'Could not create applications. Possible duplicate candidate entry.'
                ]
            })

        # enqueue resume parsing
        from onboarding.utils.task_queue import TASK_QUEUE
        from .utils import parse_resume_task

        for application in created_applications:
            TASK_QUEUE.enqueue(
                parse_resume_task,
                application,
                application.resume.file,
                link.job
            )

        return created_applications

class JobApplicationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating job application"""
    
    class Meta:
        model = JobApplication
        fields = ['status', 'notes', 'rating', 'candidate_name','candidate_phone','candidate_email',
                  'source','experience_years','relevant_experience_years','location','skill',
                  'education','current_employer','linkedin_url','job'
                  ]
    
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
    internal_hr_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_internal_hr_ids(self, value):
        users = User.objects.filter(
            id__in=value,
            is_active=True,
            role__in=['hr', 'hr_manager', 'admin']
        )

        if len(users) != len(value):
            raise serializers.ValidationError(
                "One or more users are invalid or not internal HR"
            )

        return value

class ReferralApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for direct resume upload through links - NO FORM REQUIRED"""

    # resume = serializers.FileField(required=True)
    resumes = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=True
    )

    class Meta:
        model = JobApplication
        fields = ['resumes']

    def validate_resumes(self, values):
        if not values:
            raise serializers.ValidationError("At least one resume file is required")

        max_size = 10 * 1024 * 1024  # 10MB
        allowed_extensions = [
            '.pdf', '.doc', '.docx', '.txt', '.rtf',
            '.jpg', '.jpeg', '.png', '.gif',
            '.odt', '.pages',
        ]

        import os
        for value in values:
            if value.size > max_size:
                raise serializers.ValidationError(
                    f"{value.name}: File size must be less than 10MB"
                )

            ext = os.path.splitext(value.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"{value.name}: Unsupported file format"
                )

        return values


    def create(self, validated_data):
        resumes = validated_data.pop('resumes')
        data = self.context['request'].data

        referral_name = data.get('referral_name', "")
        referral_email = data.get("referral_email", "")
        referral_phone = data.get("referral_phone", "")
        referral_emp_code = data.get('referral_emp_code', "")
        referral_department = data.get("referral_department", "")
        referral_designation = data.get("referral_designation", "")
        job_id = data.get('job_id')

        job = Job.objects.filter(id=job_id).first()
        created_referrals = []

        from onboarding.utils.task_queue import TASK_QUEUE
        from .utils import parse_resume_task

        try:
            with transaction.atomic():
                for resume_file in resumes:
                    original_filename = getattr(resume_file, 'name', '')
                    file_size = getattr(resume_file, 'size', 0)

                    # Create ReferralApplication
                    referral_application = ReferralApplication.objects.create(
                        resume=resume_file,
                        original_filename=original_filename,
                        file_size=file_size,
                        referral_name=referral_name,
                        referral_email=referral_email,
                        referral_phone=referral_phone,
                        referral_emp_code=referral_emp_code,
                        referral_department=referral_department,
                        referral_designation=referral_designation,
                        position_title=job.job_title if job else None
                    )

                    # Create JobApplication
                    job_application = JobApplication.objects.create(
                        job=job,
                        resume=resume_file,
                        source='referral',
                        status='received',
                        original_filename=original_filename,
                        file_size=file_size,
                        referral_name=referral_name,
                        referral_email=referral_email,
                        referral_phone = referral_phone,
                        referral_emp_code=referral_emp_code,
                        referral_department=referral_department,
                        referral_designation=referral_designation
                    )

                    TASK_QUEUE.enqueue(
                        parse_resume_task,
                        job_application,
                        job_application.resume.file,
                        job_application.job
                    )

                    created_referrals.append(referral_application)

        except IntegrityError as e:
            print(e)
            raise serializers.ValidationError({
                'non_field_errors': [
                    'Could not create application. Possible duplicate candidate entry.'
                ]
            })

        return created_referrals

class ReferralApplicationSerializer(serializers.ModelSerializer):
    """Serializer for referral applications"""
    
    resume_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = ReferralApplication
        fields = [
            'id', 'resume', 'resume_url','original_filename', 'file_size','referral_phone',
            'file_size_mb',"referral_name","referral_email","referral_emp_code","position_title",
            "referral_designation","referral_department",'notes','created_at', 'updated_at'
        ]
    
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
    
class ReferralToJobApplicationCreateSerializer(serializers.Serializer):
    """Serializer to create a JobApplication from an existing ReferralApplication"""

    referral_application_id = serializers.UUIDField(required=True)
    job_id = serializers.UUIDField(required=True)

    def validate(self, data):
        """Ensure that the ReferralApplication and Job exist"""
        try:
            referral_application = ReferralApplication.objects.get(id=data['referral_application_id'])
        except ReferralApplication.DoesNotExist:
            raise serializers.ValidationError("Referral Application not found")

        try:
            job = Job.objects.get(id=data['job_id'])
        except Job.DoesNotExist:
            raise serializers.ValidationError("Job not found")

        data['referral_application'] = referral_application
        data['job'] = job
        return data

    def create(self, validated_data):
        """Create a JobApplication from the ReferralApplication"""

        referral_application = validated_data['referral_application']
        job = validated_data['job']

        # Prepare values to create JobApplication
        resume_file = referral_application.resume
        original_filename = referral_application.original_filename
        file_size = referral_application.file_size
        referral_name = referral_application.referral_name
        referral_email = referral_application.referral_email
        referral_phone = referral_application.referral_phone
        referral_emp_code = referral_application.referral_emp_code
        referral_department = referral_application.referral_department
        referral_designation = referral_application.referral_designation

        try:
            with transaction.atomic():
                # Create the JobApplication record
                job_application = JobApplication.objects.create(
                    job=job,
                    resume=resume_file,
                    source='referral',
                    status='received',
                    original_filename=original_filename,
                    file_size=file_size,
                    referral_name=referral_name,
                    referral_email=referral_email,
                    referral_phone=referral_phone,
                    referral_emp_code=referral_emp_code,
                    referral_department=referral_department,
                    referral_designation=referral_designation
                )

                # Trigger background task for resume parsing
                from onboarding.utils.task_queue import TASK_QUEUE
                from .utils import parse_resume_task
                TASK_QUEUE.enqueue(parse_resume_task, job_application, resume_file, job)

        except Exception as e:
            raise serializers.ValidationError(f"Error occurred while creating application: {str(e)}")

        return job_application

#Career Page

class CareersApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for resume upload through careers page"""

    resumes = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=True
    )

    class Meta:
        model = JobApplication
        fields = ['resumes']

    def validate_resumes(self, values):
        if not values:
            raise serializers.ValidationError("At least one resume file is required")

        max_size = 10 * 1024 * 1024  # 10MB
        allowed_extensions = [
            '.pdf', '.doc', '.docx', '.txt', '.rtf',
            '.jpg', '.jpeg', '.png', '.gif',
            '.odt', '.pages',
        ]

        import os
        for value in values:
            if value.size > max_size:
                raise serializers.ValidationError(
                    f"{value.name}: File size must be less than 10MB"
                )

            ext = os.path.splitext(value.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"{value.name}: Unsupported file format"
                )

        return values


    def create(self, validated_data):
        resumes = validated_data.pop('resumes')
        data = self.context['request'].data

        job_id = data.get('job_id')

        job = Job.objects.filter(id=job_id).first()
        created_applications = []

        if not job:
            raise serializers.ValidationError(f"Job does not exist!")
        
        from onboarding.utils.task_queue import TASK_QUEUE
        from .utils import pre_parse_resume_task

        try:
            with transaction.atomic():
                for resume_file in resumes:
                    original_filename = getattr(resume_file, 'name', '')
                    file_size = getattr(resume_file, 'size', 0)

                    career_application = Application.objects.create(
                        resume=resume_file,
                        original_filename=original_filename,
                        file_size=file_size,
                        position_title=job.job_title if job else None,
                        source="career_page"
                    )
                    created_applications.append(career_application)
                    TASK_QUEUE.enqueue(pre_parse_resume_task, career_application, career_application.resume, job)

        except IntegrityError as e:
            print(e)
            raise serializers.ValidationError({
                'non_field_errors': [
                    'Could not create application. Possible duplicate candidate entry.'
                ]
            })

        return created_applications
    
class CareersJobListSerializer(serializers.ModelSerializer):
    """Serializer for job list view"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
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
            'expected_closure_date', 'created_at', 'mrf_requisition_no',
            'applications_count', 'is_active'
        ]
    
    def get_applications_count(self, obj):
        return obj.applications.count()
    
    def get_remaining_positions(self, obj):
        return obj.remaining_positions()


class CareersJobDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed job view"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    mrf_details = serializers.SerializerMethodField()
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
    
    def get_remaining_positions(self, obj):
        return obj.remaining_positions()

class CareerToJobApplicationCreateSerializer(serializers.Serializer):
    """Serializer to create a JobApplication from an existing Application"""

    application_id = serializers.UUIDField(required=True)
    job_id = serializers.UUIDField(required=True)

    def validate(self, data):
        """Ensure that the Application and Job exist"""
        try:
            career_application = Application.objects.get(id=data['application_id'])
        except Application.DoesNotExist:
            raise serializers.ValidationError("Career Page Application not found")

        try:
            job = Job.objects.get(id=data['job_id'])
        except Job.DoesNotExist:
            raise serializers.ValidationError("Job not found")

        data['career_application'] = career_application
        data['job'] = job
        return data

    def create(self, validated_data):
        """Create a JobApplication from the CareerApplication"""

        career_application = validated_data['career_application']
        job = validated_data['job']

        # Prepare values to create JobApplication
        resume_file = career_application.resume
        original_filename = career_application.original_filename
        file_size = career_application.file_size
        
        try:
            with transaction.atomic():
                # Create the JobApplication record
                job_application = JobApplication.objects.create(
                    job=job,
                    resume=resume_file,
                    source='career_page',
                    status='received',
                    original_filename=original_filename,
                    file_size=file_size,
                )

                # Trigger background task for resume parsing
                from onboarding.utils.task_queue import TASK_QUEUE
                from .utils import parse_resume_task
                TASK_QUEUE.enqueue(parse_resume_task, job_application, resume_file, job)

        except Exception as e:
            raise serializers.ValidationError(f"Error occurred while creating application: {str(e)}")

        return job_application

class JobMiniSerializer(serializers.ModelSerializer):
    """Serializer for job mini view"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    mrf_requisition_no = serializers.CharField(source='mrf.requisition_no', read_only=True)
    requested_by = serializers.CharField(source='mrf.requested_by', read_only=True)
    requested_by_name = serializers.CharField(source='mrf.requested_by.name', read_only=True)
    requested_by_email = serializers.CharField(source='mrf.requested_by.email', read_only=True)
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
            'expected_closure_date', 'created_at', 'mrf_requisition_no',
            'applications_count','requested_by','requested_by_name','requested_by_email'
        ]
    
    def get_applications_count(self, obj):
        return obj.applications.count()
    
    def get_remaining_positions(self, obj):
        return obj.remaining_positions()

class JobDropDownMergedSerializer(serializers.Serializer):
    # Representative job for the merged group
    id = serializers.UUIDField()
    job_title = serializers.CharField(source='rep_job_title')

    # Aggregation fields
    job_ids = serializers.ListField()

    job_details = serializers.SerializerMethodField()

    def get_job_details(self, obj):
        job_ids = obj.get('job_ids', [])
        job_map = self.context.get('job_map', {})

        jobs = [
            job_map.get(str(jid))
            for jid in job_ids
            if job_map.get(str(jid))
        ]

        return JobMiniSerializer(jobs, many=True).data

class ApplicationCreateSerializer(serializers.ModelSerializer):
    resumes = serializers.ListField(
        child=serializers.FileField(),
        write_only=True
    )

    source = serializers.ChoiceField(choices=ApplicationSource.choices)

    class Meta:
        model = Application
        fields = ['resumes', 'source']

    def validate_resumes(self, values):
        if not values:
            raise serializers.ValidationError("At least one resume required")

        max_size = 10 * 1024 * 1024
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.png']

        import os
        for file in values:
            if file.size > max_size:
                raise serializers.ValidationError(f"{file.name} too large")

            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(f"{file.name} invalid format")

        return values

    def create(self, validated_data):
        resumes = validated_data.pop('resumes')
        source = validated_data.get('source')

        request = self.context['request']
        job_id = request.data.get('job_id')

        job = Job.objects.filter(id=job_id).first()
        created = []

        if not job:
            raise serializers.ValidationError(f"Job does not exist!")

        from onboarding.utils.task_queue import TASK_QUEUE
        from .utils import pre_parse_resume_task

        with transaction.atomic():
            for file in resumes:
                app = Application.objects.create(
                    job=job,
                    source=source,
                    resume=file,
                    original_filename=file.name,
                    file_size=file.size,
                    position_title=job.job_title if job else None
                )
                created.append(app)
                
                TASK_QUEUE.enqueue(pre_parse_resume_task, app, app.resume, job)

        return created

class GeneralApplicationCreateSerializer(serializers.ModelSerializer):
    resumes = serializers.ListField(
        child=serializers.FileField(),
        write_only=True
    )
    source = serializers.ChoiceField(choices=ApplicationSource.choices, default=ApplicationSource.CAREER)

    class Meta:
        model = Application
        fields = ['resumes', 'source', 'department', 'designation']

    def validate_resumes(self, values):
        if not values:
            raise serializers.ValidationError("At least one resume required")

        max_size = 10 * 1024 * 1024
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.png']

        import os
        for file in values:
            if file.size > max_size:
                raise serializers.ValidationError(f"{file.name} too large")

            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(f"{file.name} invalid format")

        return values

    def create(self, validated_data):
        resumes = validated_data.pop('resumes')
        source = validated_data.get('source', ApplicationSource.CAREER)
        department = validated_data.get('department')
        designation = validated_data.get('designation')

        created = []
        from onboarding.utils.task_queue import TASK_QUEUE
        from .utils import pre_parse_resume_task

        with transaction.atomic():
            for file in resumes:
                app = Application.objects.create(
                    source=source,
                    department=department,
                    designation=designation,
                    resume=file,
                    original_filename=file.name,
                    file_size=file.size,
                )
                created.append(app)
                
                TASK_QUEUE.enqueue(pre_parse_resume_task, app, app.resume, None)

        return created
    
class ApplicationToJobSerializer(serializers.Serializer):
    application_ids = serializers.ListField(child=serializers.UUIDField())
    job_id = serializers.UUIDField()

    def validate(self, data):
        try:
            application_ids = data['application_ids']
            applications = Application.objects.filter(id__in=application_ids)
            if len(applications) != len(application_ids):
                raise serializers.ValidationError("One or more applications not found")
        except Application.DoesNotExist:
            raise serializers.ValidationError("Application not found")

        try:
            job = Job.objects.get(id=data['job_id'])
        except Job.DoesNotExist:
            raise serializers.ValidationError("Job not found")

        data['applications'] = applications
        data['job'] = job
        return data

    def create(self, validated_data):
        applications = validated_data['applications']
        job = validated_data['job']
        results = []

        from onboarding.utils.engine import automation_engine
        from django.utils import timezone
        from datetime import timedelta
        from .utils import build_candidate_history

        with transaction.atomic():
            for application in applications:
                job_app = JobApplication.objects.create(
                    job=job,
                    resume=application.resume,
                    source=application.source,  # dynamic
                    status='received',
                    original_filename=application.original_filename,
                    file_size=application.file_size,
                )

                history = []
                if application.candidate_email:
                    today = timezone.now()
                    six_months_ago = today - timedelta(days=6*30)
                    duplicate_application = JobApplication.objects.filter(candidate_email=application.candidate_email,created_at__gte=six_months_ago).exclude(id=job_app.id)
                    duplicated = False
                    if duplicate_application.exists():
                        print("Duplicate resume found!")
                        history = build_candidate_history(application.candidate_email,job_app.id)
                        duplicated = True

                job_app.candidate_name = application.candidate_name
                job_app.candidate_email = application.candidate_email
                job_app.candidate_phone = application.candidate_phone
                job_app.relevant_experience_years = application.relevant_experience_years
                job_app.experience_years = application.experience_years
                job_app.linkedin_url = application.linkedin_url
                job_app.current_ctc = application.current_ctc
                job_app.expected_ctc = application.expected_ctc
                job_app.portfolio_url = application.portfolio_url
                job_app.skill = application.skill
                job_app.education = application.education
                job_app.current_employer = application.current_employer
                job_app.location = application.location
                job_app.match_score = application.match_score
                job_app.resume_report = application.resume_report
                job_app.is_duplicate = duplicated
                job_app.candidate_history = history
                job_app.save()

                if job_app.is_duplicate:
                    automation_engine(job_app,job_app.status,'duplicate_rejected')
                elif job_app.match_score >= 75:
                    automation_engine(job_app,job_app.status,'shortlisted')
                results.append(job_app)
        
        return results

class ApplicationSerializer(serializers.ModelSerializer):
    resume_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    candidate_id = serializers.UUIDField(source="id", read_only=True)
    rejected_by_name = serializers.CharField(source='rejected_by.name', read_only=True)
    rejected_by_email = serializers.CharField(source='rejected_by.email', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)

    class Meta:
        model = Application
        fields = '__all__'

    def get_resume_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.resume.url) if request else obj.resume.url

    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2)
    
class ApplicationListSerializer(serializers.ModelSerializer):
    resume_url = serializers.SerializerMethodField()
    candidate_id = serializers.UUIDField(source="id", read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)

    class Meta:
        model = Application
        fields = ['candidate_id','resume_url','source','position_title','candidate_name',
                  'candidate_email','candidate_phone','location','match_score','job',
                  'resume_report','is_duplicate','current_employer','created_at','is_rejected',
                  'department', 'designation', 'department_name', 'designation_name']

    def get_resume_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.resume.url) if request else obj.resume.url

class AssignJobSerializer(serializers.Serializer):
    consultancy_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    internal_hr_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        consultancy_ids = data.get('consultancy_ids', [])
        internal_hr_ids = data.get('internal_hr_ids', [])

        if not consultancy_ids and not internal_hr_ids:
            raise serializers.ValidationError(
                "At least one of consultancy_ids or internal_hr_ids is required"
            )

        request = self.context['request']

        # Validate consultancies
        if consultancy_ids:
            consultancies = User.objects.filter(
                id__in=consultancy_ids,
                role='consultancy',
                is_active=True,
                company=request.user.company
            )
            if len(consultancies) != len(consultancy_ids):
                raise serializers.ValidationError("Invalid consultancy users")

        # Validate internal HR
        if internal_hr_ids:
            internal_hrs = User.objects.filter(
                id__in=internal_hr_ids,
                role__in=['hr', 'hr_manager','admin'],
                is_active=True,
                company=request.user.company
            )
            if len(internal_hrs) != len(internal_hr_ids):
                raise serializers.ValidationError("Invalid internal HR users")

        return data

class CareersMergedJobSerializer(serializers.Serializer):
    designation = serializers.UUIDField()
    designation_name = serializers.CharField(source='designation__name')

    department = serializers.UUIDField()
    department_name = serializers.CharField(source='department__name')

    location = serializers.CharField(source='locations')
    job_type = serializers.CharField(source='job_types')

    total_positions = serializers.IntegerField()
    total_filled = serializers.IntegerField()
    applications_count = serializers.IntegerField()

    remaining_positions = serializers.SerializerMethodField()
    job_ids = serializers.ListField()

    id = serializers.UUIDField()
    job_title = serializers.CharField()
    created_at = serializers.DateTimeField(source='youngest_created_at')

    def get_remaining_positions(self, obj):
        return obj['total_positions'] - obj['total_filled']

class SendRejectionNotificationSerializer(serializers.Serializer):
    candidate_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    candidate_id = serializers.UUIDField(required=False)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        candidate_ids = data.get('candidate_ids')
        candidate_id = data.get('candidate_id')

        if not candidate_ids and not candidate_id:
            raise serializers.ValidationError(
                "At least one of candidate_id or candidate_ids is required."
            )

        # Normalize to candidate_ids list
        if not candidate_ids and candidate_id:
            data['candidate_ids'] = [candidate_id]

        return data