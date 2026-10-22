from types import SimpleNamespace
from unittest.mock import call, patch

from django.test import SimpleTestCase

from onboarding.utils.notifications import (
    NOTIFY_INTERNAL_MAP,
    resolve_internal_emails,
)
from onboarding.utils.onboarding_tasks import _send_manager_assignment_reminders
from onboarding.utils.templates import NOTIFY_INTERNAL_HTML_TEMPLATES


class OnboardingNotificationRoutingTests(SimpleTestCase):
    def setUp(self):
        self.candidate = SimpleNamespace(
            id="candidate-id",
            candidate_name="Test Candidate",
            joining_date="2026-01-01",
            hod_email="hod@example.com",
            reporting_manager_email="reporting@example.com",
            job=SimpleNamespace(
                mrf=SimpleNamespace(
                    requested_by=SimpleNamespace(email="requester@example.com")
                )
            ),
            onboarding_form=SimpleNamespace(
                emails_to_notify="extra@example.com"
            ),
        )

    def test_work_email_reminders_include_hod_and_reporting_manager(self):
        self.assertEqual(
            NOTIFY_INTERNAL_MAP["missing_work_email_reminder"]["receivers"],
            ["hr", "it_team"],
        )
        self.assertIn(
            "department_head",
            NOTIFY_INTERNAL_MAP["work_email_reminder"]["receivers"],
        )
        self.assertNotIn(
            "reporting_manager",
            NOTIFY_INTERNAL_MAP["work_email_reminder"]["receivers"],
        )

    def test_assignment_reminders_are_separate_and_go_to_hr(self):
        self.assertEqual(
            NOTIFY_INTERNAL_MAP["hod_assignment_reminder"]["receivers"],
            ["hr", "hr_manager"],
        )
        self.assertIn(
            "reporting_manager_assignment_reminder",
            NOTIFY_INTERNAL_HTML_TEMPLATES,
        )
        rendered_template = NOTIFY_INTERNAL_HTML_TEMPLATES[
            "reporting_manager_assignment_reminder"
        ].format(candidate=self.candidate)
        self.assertIn("Test Candidate", rendered_template)
        self.assertIn("2026-01-01", rendered_template)

    @patch("onboarding.utils.onboarding_tasks.notify_internal")
    def test_only_sends_reminders_for_missing_managers(self, notify):
        self.candidate.hod_email = None
        self.candidate.reporting_manager_email = "reporting@example.com"

        _send_manager_assignment_reminders(self.candidate)

        notify.assert_called_once_with(
            self.candidate,
            "hod_assignment_reminder",
        )

        notify.reset_mock()
        self.candidate.hod_email = "hod@example.com"
        self.candidate.reporting_manager_email = None

        _send_manager_assignment_reminders(self.candidate)

        notify.assert_called_once_with(
            self.candidate,
            "reporting_manager_assignment_reminder",
        )

    @patch("onboarding.utils.onboarding_tasks.notify_internal")
    def test_sends_both_separate_reminders_when_both_fields_are_missing(self, notify):
        self.candidate.hod_email = None
        self.candidate.reporting_manager_email = None

        _send_manager_assignment_reminders(self.candidate)

        self.assertEqual(
            notify.call_args_list,
            [
                call(self.candidate, "hod_assignment_reminder"),
                call(self.candidate, "reporting_manager_assignment_reminder"),
            ],
        )

    @patch("onboarding.utils.onboarding_tasks.notify_internal")
    def test_sends_no_assignment_reminders_when_both_managers_are_assigned(self, notify):
        _send_manager_assignment_reminders(self.candidate)

        notify.assert_not_called()
        self.assertEqual(
            NOTIFY_INTERNAL_MAP["reporting_manager_assignment_reminder"]["receivers"],
            ["hr", "hr_manager"],
        )

    def test_onboarding_hod_notice_uses_only_explicit_hod_email(self):
        recipients = resolve_internal_emails(
            self.candidate,
            ["department_head"],
            strict_hod_email=True,
        )

        self.assertEqual(recipients, ["hod@example.com"])

    def test_onboarding_hod_notice_does_not_fallback_when_hod_is_missing(self):
        self.candidate.hod_email = None

        recipients = resolve_internal_emails(
            self.candidate,
            ["department_head"],
            strict_hod_email=True,
        )

        self.assertEqual(recipients, [])

    def test_reporting_manager_resolves_from_application_field(self):
        recipients = resolve_internal_emails(
            self.candidate,
            ["reporting_manager"],
            strict_hod_email=True,
        )

        self.assertIn("reporting@example.com", recipients)
