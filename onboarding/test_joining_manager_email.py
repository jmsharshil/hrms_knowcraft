from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from onboarding.utils.joining_manager_email import (
    _resolve_teams_user,
    send_joining_day_manager_email,
)


class TeamsUserResolutionTests(SimpleTestCase):
    @patch("onboarding.utils.joining_manager_email.requests.get")
    @patch("slots.graph.get_graph_token", return_value="graph-token")
    def test_resolves_name_and_email_using_graph(self, _get_token, get):
        get.return_value.json.return_value = {
            "value": [{
                "displayName": "Team Manager",
                "mail": "manager@example.com",
                "userPrincipalName": "manager@example.com",
            }]
        }

        resolved = _resolve_teams_user("Team Manager")

        self.assertEqual(
            resolved,
            {"name": "Team Manager", "email": "manager@example.com"},
        )
        self.assertEqual(
            get.call_args.kwargs["params"]["$filter"],
            "displayName eq 'Team Manager'",
        )

    @patch("onboarding.utils.joining_manager_email.requests.get")
    @patch("slots.graph.get_graph_token", return_value="graph-token")
    def test_uses_user_principal_name_when_mail_is_empty(self, _get_token, get):
        get.return_value.json.return_value = {
            "value": [{
                "displayName": "HOD",
                "mail": "",
                "userPrincipalName": "hod@example.com",
            }]
        }

        resolved = _resolve_teams_user("hod@example.com")

        self.assertEqual(
            resolved,
            {"name": "HOD", "email": "hod@example.com"},
        )


class JoiningDayManagerEmailTests(SimpleTestCase):
    def setUp(self):
        self.application = SimpleNamespace(
            pk="application-id",
            candidate_name="Candidate Name",
            candidate_email="candidate@example.com",
            work_email="",
            hod_email="hod@example.com",
            reporting_manager_email="reporting@example.com",
            is_joining_day_manager_email_sent=False,
            onboarding_form=SimpleNamespace(team_manager="Team Manager"),
        )
        self.managers = {
            "hod@example.com": {"name": "Department Head", "email": "hod@example.com"},
            "Team Manager": {"name": "Team Manager", "email": "team@example.com"},
            "reporting@example.com": {
                "name": "Reporting Manager",
                "email": "reporting@example.com",
            },
        }

    @override_settings(ONBOARDING_DEBUG_MINUTES=False)
    @patch("onboarding.models.EmailLog.objects.filter")
    @patch("onboarding.utils.joining_manager_email.send_email")
    @patch("onboarding.utils.joining_manager_email._resolve_teams_user")
    def test_sends_to_candidate_with_all_manager_names_when_resolved(
        self, resolve_user, send_email_mock, email_log_filter
    ):
        resolve_user.side_effect = self.managers.get
        email_log_filter.return_value.order_by.return_value.first.return_value = (
            SimpleNamespace(status="sent")
        )

        sent = send_joining_day_manager_email(self.application)

        self.assertTrue(sent)
        send_email_mock.assert_called_once()
        args = send_email_mock.call_args.kwargs
        self.assertEqual(args["to"], "candidate@example.com")
        self.assertEqual(args["cc"], [])
        self.assertFalse(args["use_default_cc"])
        self.assertEqual(args["event"], "joining_day_manager_notification")
        self.assertEqual(args["email_type"], "candidate")
        self.assertIn("Mr. Team Manager’s team", args["text"])
        self.assertIn("Reporting Manager", args["text"])
        self.assertIn("Your HOD will be Department Head", args["text"])
        self.assertEqual(
            email_log_filter.call_args.kwargs["recipient_email"],
            "candidate@example.com",
        )

    @override_settings(ONBOARDING_DEBUG_MINUTES=False)
    @patch("onboarding.utils.joining_manager_email.send_email")
    @patch("onboarding.utils.joining_manager_email._resolve_teams_user")
    def test_does_not_send_when_candidate_email_is_missing(
        self, resolve_user, send_email_mock
    ):
        self.application.candidate_email = ""
        self.application.work_email = ""

        sent = send_joining_day_manager_email(self.application)

        self.assertFalse(sent)
        resolve_user.assert_not_called()
        send_email_mock.assert_not_called()

    @patch("onboarding.utils.joining_manager_email._resolve_teams_user")
    @patch("onboarding.utils.joining_manager_email.send_email")
    def test_waits_until_all_manager_values_are_provided(
        self, send_email_mock, resolve_user
    ):
        self.application.hod_email = ""

        sent = send_joining_day_manager_email(self.application)

        self.assertFalse(sent)
        resolve_user.assert_not_called()
        send_email_mock.assert_not_called()

    @patch("onboarding.utils.joining_manager_email._resolve_teams_user")
    @patch("onboarding.utils.joining_manager_email.send_email")
    def test_skips_private_jobs(self, send_email_mock, resolve_user):
        self.application.job = SimpleNamespace(is_private=True, pk="private-job")

        sent = send_joining_day_manager_email(self.application)

        self.assertFalse(sent)
        resolve_user.assert_not_called()
        send_email_mock.assert_not_called()

    @patch("onboarding.models.EmailLog.objects.filter")
    @patch("onboarding.utils.joining_manager_email.send_email")
    @patch("onboarding.utils.joining_manager_email._resolve_teams_user")
    def test_does_not_report_failed_delivery_as_sent(
        self, resolve_user, send_email_mock, email_log_filter
    ):
        resolve_user.side_effect = self.managers.get
        email_log_filter.return_value.order_by.return_value.first.return_value = (
            SimpleNamespace(status="failed")
        )

        sent = send_joining_day_manager_email(self.application)

        self.assertFalse(sent)
