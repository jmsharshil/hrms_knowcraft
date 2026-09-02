from django.contrib import admin
from .models import Booking, GraphEventLog, SystemLock
from django.utils.html import format_html
from django.urls import reverse
# Register your models here.


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'candidate_link', 'interviewer', 'interview_type',
        'start', 'end', 'location', 'meeting_link_display',
        'has_transcript', 'created_at'
    )
    list_filter = ('interview_type', 'created_at', 'start', 'location')
    search_fields = (
        'candidate__candidate_name', 'candidate__candidate_email',
        'interviewer__name', 'meeting_id', 'location__name'
    )
    readonly_fields = ('id', 'created_at', 'meeting_id', 'meeting_link', 'transcript', 'recording_url')
    filter_horizontal = ('attendees',)
    date_hierarchy = 'start'

    fieldsets = (
        ('Core Booking Details', {
            'fields': (
                'id', 'candidate', 'interviewer', 'interview_type',
                'slot', 'location', 'start', 'end'
            )
        }),
        ('Microsoft Teams / Graph Integration', {
            'fields': (
                'meeting_id', 'meeting_link', 'transcript', 'recording_url', 'attendees'
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def candidate_link(self, obj):
        url = reverse("admin:jobs_jobapplication_change", args=[obj.candidate.id])
        return format_html('<a href="{}">{}</a>', url, obj.candidate.candidate_name)
    candidate_link.short_description = 'Candidate'
    candidate_link.admin_order_field = 'candidate__candidate_name'

    def meeting_link_display(self, obj):
        if obj.meeting_link:
            return format_html('<a href="{}" target="_blank">Join Meeting</a>', obj.meeting_link)
        return "—"
    meeting_link_display.short_description = 'Meeting Link'

    def has_transcript(self, obj):
        return bool(obj.transcript)
    has_transcript.boolean = True
    has_transcript.short_description = 'Has Transcript'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'candidate', 'interviewer', 'location', 'slot'
        ).prefetch_related('attendees')

    actions = ['cancel_selected_bookings']

    def cancel_selected_bookings(self, request, queryset):
        """Bulk cancel selected bookings (calls the view logic if possible)."""
        from booking.views import ManageBookingView
        count = 0
        for booking in queryset:
            try:
                # Simulate cancellation via the view's logic
                view = ManageBookingView()
                view.cancel_booking(request, booking.id)  # may need adjustment
                count += 1
            except Exception as e:
                self.message_user(request, f"Failed to cancel {booking}: {e}", level='error')
        self.message_user(request, f"Successfully cancelled {count} booking(s).")
    cancel_selected_bookings.short_description = "Cancel selected bookings (sync with Graph)"


@admin.register(GraphEventLog)
class GraphEventLogAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'change_type', 'subscription_id', 'created_at')
    list_filter = ('change_type', 'created_at')
    search_fields = ('event_id', 'subscription_id', 'resource')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Event Details', {
            'fields': ('event_id', 'change_type', 'subscription_id', 'resource')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )


@admin.register(SystemLock)
class SystemLockAdmin(admin.ModelAdmin):
    list_display = ('key', 'locked_at')
    readonly_fields = ('key', 'locked_at')
    list_filter = ('locked_at',)
    search_fields = ('key',)

    def has_add_permission(self, request):
        return False  # System locks should be managed programmatically

    def has_delete_permission(self, request, obj=None):
        return False
