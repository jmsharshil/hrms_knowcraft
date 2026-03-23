import django_filters
from django.db.models import Q
from .models import JobApplication,Application
from django.db.models.functions import Cast
from django.db.models import FloatField

class UUIDInFilter(django_filters.BaseInFilter, django_filters.UUIDFilter):
    """Filter for multiple UUIDs"""
    pass

class JobApplicationFilter(django_filters.FilterSet):
    # =============================
    # BASIC APPLICATION FILTERS
    # =============================
    status = django_filters.CharFilter(field_name='status')
    source = django_filters.CharFilter(field_name='source')
    submitted_by = django_filters.UUIDFilter(field_name='submitted_by_id')

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
        if request and hasattr(request.user, 'company'):
            # Filter the base queryset to only include this company
            self.queryset = self.queryset.filter(job__company=request.user.company)

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(candidate_name__icontains=value) |
            Q(candidate_email__icontains=value) |
            Q(candidate_phone__icontains=value) |
            Q(job__job_title__icontains=value)
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
        model = Application
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = getattr(self, 'request', None)
        if request and hasattr(request.user, 'company'):
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