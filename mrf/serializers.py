from rest_framework import serializers

from slots.models import Interviewer
from .models import (
    Department, Designation, MRF, MRFApproval, MRFRevision, 
    ApprovalWorkflow, WorkflowTemplate
)
from accounts.models import User
from django.db import transaction
from datetime import datetime

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = ['id', 'name', 'code', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = ApprovalWorkflow
        fields = [
            'id', 'template', 'template_name', 'level', 'required_role', 
            'is_active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ApprovalWorkflowCreateSerializer(serializers.ModelSerializer):
    """
    Used ONLY for nested creation inside WorkflowTemplate.
    Note: template field is NOT present here because we assign it after template creation.
    """
    id = serializers.UUIDField(required=False)  # allow client to omit id

    class Meta:
        model = ApprovalWorkflow
        fields = ['id', 'level', 'required_role', 'is_active', 'order']
        read_only_fields = ['id']

    def validate_level(self, value):
        if value < 1:
            raise serializers.ValidationError("level must be >= 1")
        return value

class WorkflowTemplateSerializer(serializers.ModelSerializer):
    # Accept nested levels (writable on create)
    levels = ApprovalWorkflowCreateSerializer(many=True, required=False)
    total_levels = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowTemplate
        fields = [
            'id', 'name', 'description', 'is_active', 'is_default',
            'levels', 'total_levels', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_levels(self, obj):
        return obj.levels.filter(is_active=True).count()

    def validate(self, data):
        """
        Basic validation on nested levels: ensure duplicate 'level' values are not provided.
        """
        levels_data = data.get('levels', [])
        if levels_data:
            seen = set()
            for idx, lvl in enumerate(levels_data):
                lv = lvl.get('level')
                if lv in seen:
                    raise serializers.ValidationError({
                        'levels': f"Duplicate level '{lv}' in levels payload (index {idx})."
                    })
                seen.add(lv)
        return data

    @transaction.atomic
    def create(self, validated_data):
        """
        Create WorkflowTemplate and nested ApprovalWorkflow(s) in one transaction.
        This does *not* change how ApprovalWorkflowViewSet works — nested write support
        is only for template creation (POST /workflow-templates/).
        """
        levels_data = validated_data.pop('levels', [])

        # Create the template (this will execute WorkflowTemplate.save() logic which
        # ensures only one default template exists)
        template = super().create(validated_data)

        # Create levels if provided
        created_levels = []
        for lvl in levels_data:
            # Remove 'id' if present - we let DB generate a new id for nested-created levels
            lvl.pop('id', None)
            # Create ApprovalWorkflow pointing to this template
            created = ApprovalWorkflow.objects.create(template=template, **lvl)
            created_levels.append(created)

        # Attach created_levels to serializer.instance so nested data appears in response
        # (prefetching is not strictly necessary but keeps response consistent)
        template = WorkflowTemplate.objects.prefetch_related('levels').get(pk=template.pk)
        return template

# class WorkflowTemplateSerializer(serializers.ModelSerializer):
#     levels = ApprovalWorkflowSerializer(many=True, read_only=True)
#     total_levels = serializers.SerializerMethodField()
    
#     class Meta:
#         model = WorkflowTemplate
#         fields = [
#             'id', 'name', 'description', 'is_active', 'is_default', 
#             'levels', 'total_levels', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'created_at', 'updated_at']
    
#     def get_total_levels(self, obj):
#         return obj.levels.filter(is_active=True).count()


class WorkflowTemplateSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing"""
    total_levels = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowTemplate
        fields = ['id', 'name', 'description', 'is_active', 'is_default', 'total_levels']
    
    def get_total_levels(self, obj):
        return obj.levels.filter(is_active=True).count()


class MRFApprovalSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source='approver.name', read_only=True)
    approver_email = serializers.CharField(source='approver.email', read_only=True)
    approver_role = serializers.CharField(source='approver.get_role_display', read_only=True)
    
    class Meta:
        model = MRFApproval
        fields = [
            'id', 'level', 'approver', 'approver_name', 'approver_email', 
            'approver_role', 'action', 'comments', 'rejection_reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MRFRevisionSerializer(serializers.ModelSerializer):
    revised_by_name = serializers.CharField(source='revised_by.name', read_only=True)
    
    class Meta:
        model = MRFRevision
        fields = ['id', 'revised_by', 'revised_by_name', 'revision_notes', 'previous_data', 'created_at']
        read_only_fields = ['id', 'created_at']


class MRFListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    workflow_name = serializers.CharField(source='workflow_template.name', read_only=True)
    
    class Meta:
        model = MRF
        fields = [
            'mrf_name',
            'id', 'requisition_no', 'department_name', 'designation_name', 
            'no_of_vacancies', 'location', 'job_type', 'status', 'status_display',
            'requested_by_name', 'workflow_name', 'date_of_request', 
            'created_at', 'updated_at'
        ]


class MRFDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single MRF view"""
    mrf_name = serializers.CharField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    position_department_name = serializers.CharField(source='position_department.name', read_only=True)
    requested_by_email = serializers.CharField(source='requested_by.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    location_display = serializers.CharField(source='get_location_display', read_only=True)
    job_type_display = serializers.CharField(source='get_job_type_display', read_only=True)
    case_study_required_display = serializers.CharField(source='get_case_study_required_display', read_only=True)
    workflow_name = serializers.CharField(source='workflow_template.name', read_only=True)
    workflow_summary = serializers.SerializerMethodField()
    
    approvals = MRFApprovalSerializer(many=True, read_only=True)
    revisions = MRFRevisionSerializer(many=True, read_only=True)
    
    next_approvers = serializers.SerializerMethodField()
    can_approve = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = MRF
        fields = '__all__'
        read_only_fields = [
            'mrf_name',
            'id', 'requisition_no', 'date_received', 'status',
            'current_approval_level', 'created_at', 'updated_at', 
            'submitted_at', 'approved_at', 'requested_by', 
            'requested_by_name', 'requested_by_designation', 'workflow_template'
        ]
    
    def get_workflow_summary(self, obj):
        return obj.get_workflow_summary()
    
    def get_next_approvers(self, obj):
        approvers = obj.get_next_approvers()
        return [{'id': str(u.id), 'name': u.name, 'email': u.email, 'role': u.get_role_display()} for u in approvers]
    
    def get_can_approve(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.can_user_approve(request.user)
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        user = request.user
        # Only creator can edit in draft or revision_required status
        return obj.requested_by == user and obj.status in ['draft', 'revision_required']
    
    def get_interviewers(self, obj):
        emails = [
            obj.interviewer_email_1,
            obj.interviewer_email_2,
            obj.interviewer_email_final
        ]

        result = []

        for email in [e for e in emails if e]:
            interviewer = Interviewer.objects.filter(email=email).first()

            result.append({
                "interviewer_id": interviewer.id if interviewer else None,
                "name": email.split("@")[0].replace(".", " ").title(),
                "email": email
            })

        return result


class MRFCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating MRFs"""
    workflow_template = serializers.PrimaryKeyRelatedField(
        queryset=WorkflowTemplate.objects.filter(is_active=True),
        required=False,
        help_text="If not provided, the default workflow will be used"
    )
    
    class Meta:
        model = MRF
        fields = [
            'mrf_name',
            'workflow_template', 'department', 'designation', 'team', 'position_department',
            'no_of_vacancies', 'location', 'resigned_crafter_name', 'resigned_crafter_ecode',
            'key_responsibility', 'required_qualifications', 'experience_range',
            'skills_competencies', 'business_justification','job_type',
            'expected_date_of_joining', 'case_study_required', 'technical_interview_1',
            'technical_interview_2', 'final_interview',
            'interviewer_email_1','interviewer_email_2','interviewer_email_final'
        ]
    
    def validate(self, data):
        # Auto-fill position_department from department if not provided
        if 'position_department' not in data or not data.get('position_department'):
            data['position_department'] = data.get('department')

        if 'salary_range' in data and data.get("salary_range"):
            department_name = data.get('department')
            designation_name = data.get('designation')
            salary_range = data.get('salary_range')
            from .utils import validate_salary_range
            validate_salary_range(salary_range,department_name,designation_name)
        
        # Validate dates
        if data.get('expected_date_of_joining'):
            from django.utils import timezone
            if data['expected_date_of_joining'] < timezone.now().date():
                raise serializers.ValidationError({
                    'expected_date_of_joining': 'Expected date of joining cannot be in the past'
                })
        
        # Assign default workflow if not provided
        if 'workflow_template' not in data or not data.get('workflow_template'):
            default_workflow = WorkflowTemplate.objects.filter(
                is_active=True, 
                is_default=True
            ).first()
            
            if not default_workflow:
                # If no default, get the first active workflow
                default_workflow = WorkflowTemplate.objects.filter(is_active=True).first()
            
            if not default_workflow:
                raise serializers.ValidationError({
                    'workflow_template': 'No active workflow template found. Please create one first.'
                })
            
            data['workflow_template'] = default_workflow
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Set requested_by fields
        validated_data['requested_by'] = user
        validated_data['requested_by_name'] = user.name
        validated_data['requested_by_designation'] = user.role
        from .utils import get_auto_salary_range
        salary_range = get_auto_salary_range(validated_data['department'],validated_data['designation'])
        if salary_range:
            validated_data['salary_range'] = salary_range   
        mrf = MRF.objects.create(**validated_data)
        return mrf
    
    def update(self, instance, validated_data):
        # Store previous data for revision tracking
        if instance.status == 'revision_required':
            previous_data = {
                'department': str(instance.department.id),
                'designation': str(instance.designation.id),
                'no_of_vacancies': instance.no_of_vacancies,
                'key_responsibility': instance.key_responsibility,
                # Add other relevant fields
            }
            
            MRFRevision.objects.create(
                mrf=instance,
                revised_by=self.context['request'].user,
                revision_notes=self.context.get('revision_notes', 'Revised after rejection'),
                previous_data=previous_data
            )
        
        # Don't allow workflow_template change after creation
        validated_data.pop('workflow_template', None)
        
        if 'position_department' in validated_data:
            if not validated_data.get('position_department'):
                validated_data['position_department'] = (
                    validated_data.get('department') or instance.department
                )
        else:
            if 'department' in validated_data and validated_data.get('department'):
                validated_data['position_department'] = validated_data.get('department')
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class MRFSubmitSerializer(serializers.Serializer):
    """Serializer for submitting MRF for approval"""
    def submit(self):
        mrf = self.context['mrf']   # mrf instance passed from view
        user = self.context['request'].user
        from onboarding.utils.sender import send_email
        subject = f'Requisition Raised for {mrf.designation} Position'
        manager_name = User.objects.filter(role="hr_manager").first().name
        manager_email = User.objects.filter(role="hr_manager").first().email
        from .utils import email_templates,alt_text
        if mrf.resigned_crafter_name:
            template = email_templates['mrf_submit_replace']
            template = template.format(manager_name=manager_name,hod_name=mrf.requested_by.name,designation=mrf.designation.name,date=mrf.created_at.strftime("%B %d,%Y"),resigned_employee=mrf.resigned_crafter_name)
            text = alt_text['mrf_submit_replace']
            text = text.format(manager_name=manager_name,hod_name=mrf.requested_by.name,designation=mrf.designation.name,date=mrf.created_at.strftime("%B %d,%Y"),resigned_employee=mrf.resigned_crafter_name)
        else:
            template = email_templates['mrf_submit_new']
            template = template.format(manager_name=manager_name,hod_name=mrf.requested_by.name,designation=mrf.designation.name,date=mrf.created_at.strftime("%B %d,%Y"))
            text = alt_text['mrf_submit_new']
            text = text.format(manager_name=manager_name,hod_name=mrf.requested_by.name,designation=mrf.designation.name,date=mrf.created_at.strftime("%B %d,%Y"))
        try:
            send_email(to=manager_email,subject=subject,template=template,text=text)
            from .utils import schedule_mrf_reminder
            schedule_mrf_reminder(mrf_id=mrf.id)
        except Exception as e:
            print(f"Error Occured while trying to send email for MRF Approval:{e}")

class MRFApproveRejectSerializer(serializers.Serializer):
    """Serializer for approving or rejecting MRF"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    comments = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting an MRF'
            })
        return data