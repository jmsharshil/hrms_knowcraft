import django_filters
from django.db.models import Q
from .models import JobApplication
from django.db.models.functions import Cast
from django.db.models import FloatField


class JobApplicationFilter(django_filters.FilterSet):
    # =============================
    # BASIC APPLICATION FILTERS
    # =============================
    job = django_filters.UUIDFilter(field_name='job_id')
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

    assigned_hr = django_filters.UUIDFilter(
        field_name='job__assigned_to_internal_hr_id'
    )

    assigned_consultancy = django_filters.UUIDFilter(
        field_name='job__assigned_to_consultancy_id'
    )

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
            Q(candidate_phone__icontains=value)
        )
