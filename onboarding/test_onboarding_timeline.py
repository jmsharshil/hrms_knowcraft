from datetime import timedelta
from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from onboarding.utils.onboarding_tasks import (
    DEBUG_ONBOARDING_MILESTONES,
    get_days_until_joining,
)


class OnboardingTimelineTests(SimpleTestCase):
    @override_settings(ONBOARDING_DEBUG_MINUTES=True)
    def test_debug_timeline_advances_through_all_milestones_and_stays_at_last(self):
        start = timezone.now()
        candidate = SimpleNamespace(
            candidate_name="Test Candidate",
            created_at=start,
            joining_date=start.date(),
        )

        for minute, expected_day in DEBUG_ONBOARDING_MILESTONES:
            with self.subTest(minute=minute):
                self.assertEqual(
                    get_days_until_joining(
                        candidate,
                        now=start + timedelta(minutes=minute),
                    ),
                    expected_day,
                )

        self.assertEqual(
            get_days_until_joining(
                candidate,
                now=start + timedelta(minutes=13),
            ),
            -90,
        )
        self.assertEqual(
            get_days_until_joining(
                candidate,
                now=start + timedelta(minutes=120),
            ),
            -90,
        )

    @override_settings(ONBOARDING_DEBUG_MINUTES=False)
    def test_non_debug_timeline_uses_joining_date(self):
        now = timezone.now()
        candidate = SimpleNamespace(
            candidate_name="Test Candidate",
            created_at=now - timedelta(days=100),
            joining_date=now.date() + timedelta(days=15),
        )

        self.assertEqual(get_days_until_joining(candidate, now=now), 15)
