import django_filters
from django.db.models import Q
from .models import JobApplication,Application,ReferralApplication
from bgv.models import CandidateBGV
from django.db.models.functions import Cast
from django.db.models import FloatField

class UUIDInFilter(django_filters.BaseInFilter, django_filters.UUIDFilter):
    """Filter for multiple UUIDs"""
    pass

class JobApplicationFilter(django_filters.FilterSet):
    # =============================
    # BASIC APPLICATION FILTERS
    # =============================
    job_id = django_filters.CharFilter(method='filter_job')
    status = django_filters.CharFilter(field_name='status')
    source = django_filters.CharFilter(field_name='source')
    submitted_by = django_filters.UUIDFilter(field_name='submitted_by_id')

    # =============================
    # REFERRAL FILTERS (for referral job applications)
    # =============================
    referral_name = django_filters.CharFilter(
        field_name='referral_name', lookup_expr='icontains'
    )
    referral_email = django_filters.CharFilter(
        field_name='referral_email', lookup_expr='icontains'
    )
    referral_emp_code = django_filters.CharFilter(
        field_name='referral_emp_code', lookup_expr='icontains'
    )

    # =============================
    # PLATFORM FILTER (IMPORTANT)
    # =============================
    platform = django_filters.CharFilter(
        field_name='application_link__platform'
    )

    # =============================
    # JOB-RELATED FILTERS
    # =============================
    job_status = django_filters.CharFilter(
        field_name='job__status'
    )

    job_type = django_filters.CharFilter(
        field_name='job__job_type'
    )

    department = django_filters.UUIDFilter(
        field_name='job__department_id'
    )

    assigned_hr = django_filters.UUIDFilter(method='filter_assigned_hr')

    assigned_consultancy = django_filters.UUIDFilter(method='filter_assigned_consultancy')

    assigned_to_me = django_filters.BooleanFilter(method='filter_assigned_to_me')

    # =============================
    # EXPERIENCE & SCORE FILTERS
    # =============================
    min_experience = django_filters.NumberFilter(
        field_name='experience_years',
        lookup_expr='gte'
    )

    max_experience = django_filters.NumberFilter(
        field_name='experience_years',
        lookup_expr='lte'
    )

    min_match_score = django_filters.NumberFilter(
        method='filter_min_match_score'
    )

    def filter_min_match_score(self, queryset, name, value):
        return queryset.annotate(
            match_score_float=Cast('match_score', FloatField())
        ).filter(match_score_float__gte=value)

    def filter_assigned_hr(self, queryset, name, value):
        return queryset.filter(
            Q(job__assigned_to_internal_hr_id=value) |
            Q(job__assigned_internal_hrs__id=value)
        )


    def filter_assigned_consultancy(self, queryset, name, value):
        return queryset.filter(
            Q(job__assigned_to_consultancy_id=value) |
            Q(job__assigned_consultancies__id=value)
        )
    
    def filter_assigned_to_me(self, queryset, name, value):
        user = self.request.user

        if not value or not user.is_authenticated:
            return queryset

        if user.role == 'consultancy':
            return queryset.filter(
                Q(job__assigned_to_consultancy=user) |
                Q(job__assigned_consultancies=user)
            ).distinct()

        elif user.role in ['hr', 'hr_manager', 'admin']:
            return queryset.filter(
                Q(job__assigned_to_internal_hr=user) |
                Q(job__assigned_internal_hrs=user)
            ).distinct()

        return queryset.none()
    
    # =============================
    # DATE FILTERS
    # =============================
    created_from = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__gte'
    )

    created_to = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__lte'
    )

    # =============================
    # SEARCH FILTER
    # =============================
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = JobApplication
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = getattr(self, 'request', None)
        if request and hasattr(request, 'user') and hasattr(request.user, 'company'):
            # Filter the base queryset to only include this company
            self.queryset = self.queryset.filter(job__company=request.user.company)

    def filter_search(self, queryset, name, value):
        """Search across candidate details, job title, department name, designation name,
        and referral fields (for referral job applications). This is used by JobApplicationViewSet.
        Note: The view's get_queryset no longer applies a limiting candidate-only search,
        allowing these job-related fields to be searchable."""
        return queryset.filter(
            Q(candidate_name__icontains=value) |
            Q(candidate_email__icontains=value) |
            Q(candidate_phone__icontains=value) |
            Q(job__job_title__icontains=value) |
            Q(referral_name__icontains=value) |
            Q(referral_email__icontains=value) |
            Q(referral_phone__icontains=value) |
            Q(referral_emp_code__icontains=value) |
            Q(job__department__name__icontains=value) |
            Q(job__designation__name__icontains=value)
        )

    def filter_job(self, queryset, name, value):
        request = self.request
        import uuid

        raw_values = request.GET.getlist('job_id')

        job_ids = []

        for val in raw_values:
            if ',' in val:
                job_ids.extend([v.strip() for v in val.split(',') if v.strip()])
            else:
                job_ids.append(val.strip())

        # Validate UUIDs
        valid_ids = []
        for j in job_ids:
            try:
                valid_ids.append(str(uuid.UUID(j)))
            except Exception:
                pass

        # 🚨 IMPORTANT: return EMPTY queryset if invalid input
        if not valid_ids:
            return queryset.none()

        return queryset.filter(job_id__in=valid_ids)
    

class ApplicationFilter(django_filters.FilterSet):
    # =============================
    # BASIC APPLICATION FILTERS
    # =============================
    job_id = django_filters.CharFilter(method='filter_job')
    source = django_filters.CharFilter(field_name='source')

    # =============================
    # JOB-RELATED FILTERS
    # =============================
    job_status = django_filters.CharFilter(
        field_name='job__status'
    )

    job_type = django_filters.CharFilter(
        field_name='job__job_type'
    )

    department = django_filters.UUIDFilter(method='filter_department')
    designation = django_filters.UUIDFilter(method='filter_designation')

    assigned_hr = django_filters.UUIDFilter(method='filter_assigned_hr')

    assigned_consultancy = django_filters.UUIDFilter(method='filter_assigned_consultancy')

    assigned_to_me = django_filters.BooleanFilter(method='filter_assigned_to_me')

    # =============================
    # EXPERIENCE & SCORE FILTERS
    # =============================
    min_experience = django_filters.NumberFilter(
        field_name='experience_years',
        lookup_expr='gte'
    )

    max_experience = django_filters.NumberFilter(
        field_name='experience_years',
        lookup_expr='lte'
    )

    min_match_score = django_filters.NumberFilter(
        method='filter_min_match_score'
    )

    def filter_min_match_score(self, queryset, name, value):
        return queryset.annotate(
            match_score_float=Cast('match_score', FloatField())
        ).filter(match_score_float__gte=value)

    def filter_department(self, queryset, name, value):
        return queryset.filter(
            Q(job__department_id=value) | Q(department_id=value)
        )

    def filter_designation(self, queryset, name, value):
        return queryset.filter(
            Q(job__designation_id=value) | Q(designation_id=value)
        )

    def filter_assigned_hr(self, queryset, name, value):
        return queryset.filter(
            Q(job__assigned_to_internal_hr_id=value) |
            Q(job__assigned_internal_hrs__id=value)
        )


    def filter_assigned_consultancy(self, queryset, name, value):
        return queryset.filter(
            Q(job__assigned_to_consultancy_id=value) |
            Q(job__assigned_consultancies__id=value)
        )
    
    def filter_assigned_to_me(self, queryset, name, value):
        user = self.request.user

        if not value or not user.is_authenticated:
            return queryset

        if user.role == 'consultancy':
            return queryset.filter(
                Q(job__assigned_to_consultancy=user) |
                Q(job__assigned_consultancies=user)
            ).distinct()

        elif user.role in ['hr', 'hr_manager', 'admin']:
            return queryset.filter(
                Q(job__assigned_to_internal_hr=user) |
                Q(job__assigned_internal_hrs=user)
            ).distinct()

        return queryset.none()
    
    # =============================
    # DATE FILTERS
    # =============================
    created_from = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__gte'
    )

    created_to = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__lte'
    )

    # =============================
    # SEARCH FILTER
    # =============================
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Application
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = getattr(self, 'request', None)
        if request and hasattr(request, 'user') and hasattr(request.user, 'company'):
            # Filter the base queryset to only include this company
            self.queryset = self.queryset.filter(job__company=request.user.company)

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(candidate_name__icontains=value) |
            Q(candidate_email__icontains=value) |
            Q(candidate_phone__icontains=value) |
            Q(job__job_title__icontains=value) |
            Q(position_title__icontains=value)
        )

    def filter_job(self, queryset, name, value):
        request = self.request
        import uuid

        raw_values = request.GET.getlist('job_id')

        job_ids = []

        for val in raw_values:
            if ',' in val:
                job_ids.extend([v.strip() for v in val.split(',') if v.strip()])
            else:
                job_ids.append(val.strip())

        # Validate UUIDs
        valid_ids = []
        for j in job_ids:
            try:
                valid_ids.append(str(uuid.UUID(j)))
            except Exception:
                pass

        # 🚨 IMPORTANT: return EMPTY queryset if invalid input
        if not valid_ids:
            return queryset.none()

        return queryset.filter(job_id__in=valid_ids)


class ReferralApplicationFilter(django_filters.FilterSet):
    # BASIC REFERRAL FILTERS
    referral_name = django_filters.CharFilter(field_name='referral_name', lookup_expr='icontains')
    referral_email = django_filters.CharFilter(field_name='referral_email', lookup_expr='icontains')
    referral_phone = django_filters.CharFilter(field_name='referral_phone', lookup_expr='icontains')
    referral_emp_code = django_filters.CharFilter(field_name='referral_emp_code', lookup_expr='icontains')
    position_title = django_filters.CharFilter(field_name='position_title', lookup_expr='icontains')
    is_touched = django_filters.BooleanFilter(field_name='is_touched')
    # Date filters
    created_from = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_to = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    # Search filter using method
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = ReferralApplication
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = getattr(self, 'request', None)
        if request and hasattr(request, 'user') and hasattr(request.user, 'company'):
            pass  # No company filtering for referrals currently (no FK)

    def filter_search(self, queryset, name, value):
        """Search across referral fields, position, and notes."""
        return queryset.filter(
            Q(referral_name__icontains=value) |
            Q(referral_email__icontains=value) |
            Q(referral_phone__icontains=value) |
            Q(referral_emp_code__icontains=value) |
            Q(referral_designation__icontains=value) |
            Q(referral_department__icontains=value) |
            Q(position_title__icontains=value) |
            Q(notes__icontains=value)
        )


class CandidateBGVFilter(django_filters.FilterSet):
    """
    FilterSet for CandidateBGVViewSet (and its CandidateBGVListSerializer).
    Re-uses patterns from JobApplicationFilter.
    Supports ?search= (across candidate/job fields + BGV-specific), status, is_fresher,
    date ranges, UUIDs, etc. Company scoping applied in __init__.
    """
    # =============================
    # BGV SPECIFIC FILTERS
    # =============================
    status = django_filters.ChoiceFilter(
        field_name="status", choices=CandidateBGV.STATUS_CHOICES
    )
    is_fresher = django_filters.BooleanFilter(field_name='is_fresher')
    job_id = django_filters.UUIDFilter(field_name='candidate__job_id')
    candidate_id = django_filters.UUIDFilter(field_name='candidate_id')
    ongrid_individual_id = django_filters.CharFilter(
        field_name='ongrid_individual_id', lookup_expr='icontains'
    )

    # =============================
    # DATE FILTERS
    # =============================
    bgv_scheduled_date = django_filters.DateFromToRangeFilter()
    initiated_from = django_filters.DateFilter(
        field_name='initiated_at', lookup_expr='date__gte'
    )
    initiated_to = django_filters.DateFilter(
        field_name='initiated_at', lookup_expr='date__lte'
    )
    completed_from = django_filters.DateFilter(
        field_name='completed_at', lookup_expr='date__gte'
    )
    completed_to = django_filters.DateFilter(
        field_name='completed_at', lookup_expr='date__lte'
    )

    # =============================
    # SEARCH FILTER
    # =============================
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = CandidateBGV
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = getattr(self, 'request', None)
        if (
            request
            and hasattr(request, 'user')
            and hasattr(request.user, 'company')
        ):
            # Scope to user's company (via the linked JobApplication.job.company)
            self.queryset = self.queryset.filter(
                candidate__job__company=request.user.company
            )

    def filter_search(self, queryset, name, value):
        """Search across candidate fields (name/email/phone), job title,
        OnGrid ID, BGV status, and remarks. Works with CandidateBGVListSerializer
        (which uses flattened sources like candidate.job.job_title).
        View uses select_related to avoid N+1."""
        return queryset.filter(
            Q(candidate__candidate_name__icontains=value)
            | Q(candidate__candidate_email__icontains=value)
            | Q(candidate__candidate_phone__icontains=value)
            | Q(candidate__job__job_title__icontains=value)
            | Q(ongrid_individual_id__icontains=value)
            | Q(status__icontains=value)
            | Q(remarks__icontains=value)
        )
