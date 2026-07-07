import datetime
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone

from onboarding.utils.interview_feedback_reminder import interview_feedback_reminder_task
from booking.models import Booking

class FeedbackReminderTaskTests(TestCase):

    def setUp(self):
        self.booking_id = "test-booking-123"
        
        # Setup a mock booking
        self.mock_booking = MagicMock()
        self.mock_booking.id = self.booking_id
        self.mock_booking.candidate.status = "interview_pending_1"
        self.mock_booking.candidate.candidate_name = "John Doe"
        self.mock_booking.interviewer.email = "interviewer@example.com"
        self.mock_booking.interviewer.name = "Interviewer One"
        self.mock_booking.end = timezone.now() - datetime.timedelta(minutes=45) # Already ended
        
        # Patch the Booking get method
        self.booking_patcher = patch("onboarding.utils.interview_feedback_reminder.Booking.objects.select_related")
        self.mock_select_related = self.booking_patcher.start()
        self.mock_get = self.mock_select_related.return_value.get
        self.mock_get.return_value = self.mock_booking

    def tearDown(self):
        self.booking_patcher.stop()

    def test_booking_does_not_exist(self):
        self.mock_get.side_effect = Booking.DoesNotExist
        result = interview_feedback_reminder_task(self.booking_id)
        self.assertFalse(result)

    def test_cannot_resolve_round_name(self):
        # Set candidate status to something that doesn't map to a round_name
        self.mock_booking.candidate.status = "some_unknown_status"
        self.mock_booking.candidate.round_name = None
        result = interview_feedback_reminder_task(self.booking_id)
        self.assertFalse(result)

    @patch("onboarding.utils.interview_feedback_reminder.InterviewFeedback.objects.filter")
    @patch("onboarding.utils.interview_feedback_reminder.TaskScheduler.cancel")
    def test_feedback_already_submitted(self, mock_cancel, mock_filter):
        mock_filter.return_value.exists.return_value = True
        result = interview_feedback_reminder_task(self.booking_id)
        
        mock_cancel.assert_called_once()
        self.assertFalse(result)

    @patch("onboarding.utils.interview_feedback_reminder.InterviewFeedback.objects.filter")
    @patch("onboarding.utils.interview_feedback_reminder.TaskScheduler.cancel")
    def test_candidate_status_not_pending(self, mock_cancel, mock_filter):
        mock_filter.return_value.exists.return_value = False
        
        # Status mapped to round_name but not in ROUND_PENDING_STATUS for the reminder
        # Wait, if status is interview_done_1, it will resolve to no round_name from the dictionary.
        # Let's pass round_name explicitly, but candidate status is interview_done_1
        self.mock_booking.candidate.status = "interview_done_1"
        result = interview_feedback_reminder_task(self.booking_id, round_name="hr_round")
        
        mock_cancel.assert_called_once()
        self.assertFalse(result)

    @patch("onboarding.utils.interview_feedback_reminder.InterviewFeedback.objects.filter")
    @patch("onboarding.utils.interview_feedback_reminder.TaskScheduler.schedule")
    def test_interview_not_over_yet(self, mock_schedule, mock_filter):
        mock_filter.return_value.exists.return_value = False
        
        # Interview ends in the future
        self.mock_booking.end = timezone.now() + datetime.timedelta(minutes=10)
        
        result = interview_feedback_reminder_task(self.booking_id)
        
        mock_schedule.assert_called_once()
        self.assertFalse(result)

    @patch("onboarding.utils.interview_feedback_reminder.InterviewFeedback.objects.filter")
    @patch("onboarding.utils.interview_feedback_reminder.send_feedback_reminder_email")
    def test_all_clear_sends_reminder(self, mock_send_email, mock_filter):
        mock_filter.return_value.exists.return_value = False
        
        result = interview_feedback_reminder_task(self.booking_id)
        
        mock_send_email.assert_called_once()
        self.assertTrue(result)
