from rest_framework import serializers
from .models import Department, Designation, MRF, MRFApproval, MRFRevision, ApprovalWorkflow
from accounts.models import User


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
    class Meta:
        model = ApprovalWorkflow
        fields = ['id', 'name', 'level', 'required_role', 'is_active', 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


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
    
    class Meta:
        model = MRF
        fields = [
            'id', 'requisition_no', 'department_name', 'designation_name', 
            'no_of_vacancies', 'location', 'status', 'status_display',
            'requested_by_name', 'date_of_request', 'created_at', 'updated_at'
        ]


class MRFDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single MRF view"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    position_department_name = serializers.CharField(source='position_department.name', read_only=True)
    requested_by_email = serializers.CharField(source='requested_by.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    location_display = serializers.CharField(source='get_location_display', read_only=True)
    case_study_required_display = serializers.CharField(source='get_case_study_required_display', read_only=True)
    
    approvals = MRFApprovalSerializer(many=True, read_only=True)
    revisions = MRFRevisionSerializer(many=True, read_only=True)
    
    next_approvers = serializers.SerializerMethodField()
    can_approve = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = MRF
        fields = '__all__'
        read_only_fields = [
            'id', 'requisition_no', 'date_received', 'status', 
            'current_approval_level', 'created_at', 'updated_at', 
            'submitted_at', 'approved_at', 'requested_by', 
            'requested_by_name', 'requested_by_designation'
        ]
    
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


class MRFCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating MRFs"""
    
    class Meta:
        model = MRF
        fields = [
            'department', 'designation', 'team', 'position_department',
            'no_of_vacancies', 'location', 'resigned_crafter_name', 'resigned_crafter_ecode',
            'key_responsibility', 'required_qualifications', 'experience_range',
            'skills_competencies', 'business_justification', 'salary_range',
            'expected_date_of_joining', 'case_study_required', 'technical_interview_1',
            'technical_interview_2', 'final_interview'
        ]
    
    def validate(self, data):
        # Auto-fill position_department from department if not provided
        if 'position_department' not in data or not data.get('position_department'):
            data['position_department'] = data.get('department')
        
        # Validate dates
        if data.get('expected_date_of_joining'):
            from django.utils import timezone
            if data['expected_date_of_joining'] < timezone.now().date():
                raise serializers.ValidationError({
                    'expected_date_of_joining': 'Expected date of joining cannot be in the past'
                })
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Set requested_by fields
        validated_data['requested_by'] = user
        validated_data['requested_by_name'] = user.name
        validated_data['requested_by_designation'] = user.role
        
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
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class MRFSubmitSerializer(serializers.Serializer):
    """Serializer for submitting MRF for approval"""
    pass


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