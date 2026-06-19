from django.test import TestCase
from django.test import RequestFactory
from django.db.models import Q
from jobs.models import ReferralApplication
from jobs.filters import ReferralApplicationFilter
from accounts.models import Company
from datetime import timedelta
from django.utils import timezone


class ReferralFilterTest(TestCase):
    """Test cases for ReferralApplicationFilter (and related job/application filters via seed data)"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all tests"""
        cls.company = Company.objects.create(name="Test Company")
        cls.factory = RequestFactory()
        
        # Create test referral applications (resume is now optional after model update)
        cls.ref1 = ReferralApplication.objects.create(
            referral_name="Alice Johnson",
            referral_email="alice@knowcraft.in",
            referral_phone="9876543201",
            referral_emp_code="EMP001",
            position_title="Senior Software Engineer",
            notes="Strong Python developer",
            is_touched=False,
        )
        cls.ref2 = ReferralApplication.objects.create(
            referral_name="Bob Smith",
            referral_email="bob@knowcraft.in",
            referral_phone="9876543202",
            referral_emp_code="EMP002",
            position_title="HR Executive",
            notes="HR referral",
            is_touched=True,
            touched_at=timezone.now(),
        )
        cls.ref3 = ReferralApplication.objects.create(
            referral_name="Carol Davis",
            referral_email="carol@knowcraft.in",
            referral_phone="9876543203",
            position_title="Business Development Executive",
            notes="Sales referral",
            is_touched=False,
        )

    def test_referral_filter_by_name(self):
        """Test filtering by referral_name"""
        qs = ReferralApplication.objects.all()
        f = ReferralApplicationFilter({'referral_name': 'Alice'}, queryset=qs)
        self.assertEqual(f.qs.count(), 1)
        self.assertEqual(f.qs.first().referral_name, "Alice Johnson")

    def test_referral_filter_by_email(self):
        """Test filtering by referral_email"""
        qs = ReferralApplication.objects.all()
        f = ReferralApplicationFilter({'referral_email': 'bob'}, queryset=qs)
        self.assertEqual(f.qs.count(), 1)
        self.assertEqual(f.qs.first().referral_email, "bob@knowcraft.in")

    def test_referral_filter_by_touched(self):
        """Test is_touched filter"""
        qs = ReferralApplication.objects.all()
        f = ReferralApplicationFilter({'is_touched': True}, queryset=qs)
        self.assertEqual(f.qs.count(), 1)
        self.assertTrue(f.qs.first().is_touched)

    def test_referral_search_filter(self):
        """Test the search method filter (now matches name/email/phone/emp_code/position/notes/dept/designation via Q). Tests notes-based search for 'referral job applications'."""
        qs = ReferralApplication.objects.all()
        f = ReferralApplicationFilter({'search': 'sales'}, queryset=qs)
        self.assertEqual(f.qs.count(), 1)
        self.assertEqual(f.qs.first().referral_name, "Carol Davis")
        self.assertIn("Sales", f.qs.first().notes)

    def test_referral_date_filter(self):
        """Test created_from/created_to filters"""
        qs = ReferralApplication.objects.all()
        today = timezone.now().date()
        f = ReferralApplicationFilter({
            'created_from': today - timedelta(days=1),
            'created_to': today + timedelta(days=1)
        }, queryset=qs)
        self.assertEqual(f.qs.count(), 3)  # All should match

    def test_filter_combination(self):
        """Test multiple filters together"""
        qs = ReferralApplication.objects.all()
        f = ReferralApplicationFilter({
            'search': 'Johnson',
            'is_touched': False
        }, queryset=qs)
        self.assertEqual(f.qs.count(), 1)

    def test_referral_filter_with_request(self):
        """Test filter with request object (for future company scoping)"""
        qs = ReferralApplication.objects.all()
        request = self.factory.get('/?search=carol')
        # Attach mock user to test __init__ company scoping path safely
        mock_user = type('MockUser', (), {
            'company': self.company,
            'is_authenticated': True,
            'role': 'hr'
        })()
        request.user = mock_user
        f = ReferralApplicationFilter({'search': 'carol'}, queryset=qs, request=request)
        self.assertEqual(f.qs.count(), 1)
        self.assertEqual(f.qs.first().referral_name, "Carol Davis")


