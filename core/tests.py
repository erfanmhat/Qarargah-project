from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import (
    Soldier, Leave, ServiceStatus, HealthStatus, ServiceLocation,
    ServiceReductionType, SoldierServiceReduction, SystemSetting
)


class SoldierModelTest(TestCase):
    def setUp(self):
        """Setup test data"""
        self.service_status = ServiceStatus.objects.create(
            title="در حال خدمت",
            is_active_service=True
        )
        self.health_status = HealthStatus.objects.create(
            title="سالم",
            is_exempt_from_combat=False
        )
        self.soldier = Soldier.objects.create(
            first_name="علی",
            last_name="احمدی",
            national_code="1234567890",
            dispatch_type="training",
            service_start_date=timezone.now().date() - timedelta(days=100),
            birth_date=timezone.now().date() - timedelta(days=8000),
            service_status=self.service_status,
            health_status=self.health_status
        )

    def test_soldier_creation(self):
        """Test soldier creation"""
        self.assertEqual(self.soldier.full_name(), "علی احمدی")
        self.assertEqual(str(self.soldier), "علی احمدی - 1234567890")

    def test_service_end_date_calculation(self):
        """Test service end date calculation"""
        # Default 21 months = 630 days
        end_date = self.soldier.service_end_date()
        expected_date = self.soldier.service_start_date + timedelta(days=630)
        self.assertEqual(end_date, expected_date)

    def test_service_end_date_with_reduction(self):
        """Test service end date with service reduction"""
        reduction_type = ServiceReductionType.objects.create(
            title="کسر خدمت آموزشی",
            default_days=30
        )
        SoldierServiceReduction.objects.create(
            soldier=self.soldier,
            reduction_type=reduction_type,
            days=30
        )
        end_date = self.soldier.service_end_date()
        # 630 - 30 = 600 days
        expected_date = self.soldier.service_start_date + timedelta(days=600)
        self.assertEqual(end_date, expected_date)

    def test_total_reduction_days(self):
        """Test total reduction days calculation"""
        reduction_type = ServiceReductionType.objects.create(
            title="کسر خدمت",
            default_days=10
        )
        SoldierServiceReduction.objects.create(
            soldier=self.soldier,
            reduction_type=reduction_type,
            days=10
        )
        SoldierServiceReduction.objects.create(
            soldier=self.soldier,
            reduction_type=reduction_type,
            days=20
        )
        self.assertEqual(self.soldier.total_reduction_days(), 30)

    def test_soldier_clean_validation(self):
        """Test soldier model validation"""
        # Test birth_date after service_start_date (should fail)
        soldier = Soldier(
            first_name="تست",
            last_name="تست",
            national_code="9876543210",
            dispatch_type="training",
            service_start_date=timezone.now().date(),
            birth_date=timezone.now().date() + timedelta(days=1),
            service_status=self.service_status
        )
        with self.assertRaises(Exception):
            soldier.clean()


class LeaveModelTest(TestCase):
    def setUp(self):
        """Setup test data"""
        self.service_status = ServiceStatus.objects.create(
            title="در حال خدمت",
            is_active_service=True
        )
        self.soldier = Soldier.objects.create(
            first_name="محمد",
            last_name="رضایی",
            national_code="1111111111",
            dispatch_type="training",
            service_start_date=timezone.now().date() - timedelta(days=100),
            birth_date=timezone.now().date() - timedelta(days=8000),
            service_status=self.service_status
        )

    def test_leave_creation(self):
        """Test leave creation"""
        leave = Leave.objects.create(
            soldier=self.soldier,
            leave_type="medical",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=5)
        )
        self.assertEqual(leave.days, 6)  # Including both start and end dates

    def test_leave_days_calculation(self):
        """Test leave days calculation"""
        start = timezone.now().date()
        end = start + timedelta(days=10)
        leave = Leave.objects.create(
            soldier=self.soldier,
            leave_type="reward",
            start_date=start,
            end_date=end
        )
        self.assertEqual(leave.days, 11)

    def test_leave_clean_validation(self):
        """Test leave model validation"""
        # Test end_date before start_date (should fail)
        leave = Leave(
            soldier=self.soldier,
            leave_type="medical",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() - timedelta(days=1)
        )
        with self.assertRaises(Exception):
            leave.clean()

    def test_leave_max_duration_validation(self):
        """Test leave maximum duration validation"""
        leave = Leave(
            soldier=self.soldier,
            leave_type="medical",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=31)  # More than 30 days
        )
        with self.assertRaises(Exception):
            leave.clean()


class SystemSettingTest(TestCase):
    def test_get_value_existing(self):
        """Test getting existing setting value"""
        SystemSetting.objects.create(
            key="SERVICE_MONTHS",
            value="24"
        )
        value = SystemSetting.get_value("SERVICE_MONTHS")
        self.assertEqual(value, "24")

    def test_get_value_default(self):
        """Test getting non-existing setting with default"""
        value = SystemSetting.get_value("NON_EXISTING", "default_value")
        self.assertEqual(value, "default_value")


class ViewTests(TestCase):
    def setUp(self):
        """Setup test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.service_status = ServiceStatus.objects.create(
            title="در حال خدمت",
            is_active_service=True
        )

    def test_login_view_get(self):
        """Test login page access"""
        response = self.client.get('/dashboard/login/')
        self.assertEqual(response.status_code, 200)

    def test_login_view_post_success(self):
        """Test successful login"""
        response = self.client.post('/dashboard/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login

    def test_login_view_post_failure(self):
        """Test failed login"""
        response = self.client.post('/dashboard/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page

    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_authenticated(self):
        """Test dashboard access for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_soldiers_list_authenticated(self):
        """Test soldiers list access"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/soldiers/')
        self.assertEqual(response.status_code, 200)

    def test_leaves_list_authenticated(self):
        """Test leaves list access"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/leaves/')
        self.assertEqual(response.status_code, 200)

    def test_search_page_authenticated(self):
        """Test search page access"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/search/')
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        """Test logout functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/logout/')
        self.assertEqual(response.status_code, 302)  # Redirect after logout


class FormTests(TestCase):
    def setUp(self):
        """Setup test data"""
        self.service_status = ServiceStatus.objects.create(
            title="در حال خدمت",
            is_active_service=True
        )

    def test_soldier_form_validation(self):
        """Test soldier form validation"""
        from core.forms import SoldierForm
        
        form_data = {
            'first_name': 'تست',
            'last_name': 'فرم',
            'national_code': '1234567890',
            'dispatch_type': 'training',
            'service_start_date': timezone.now().date(),
            'birth_date': timezone.now().date() - timedelta(days=8000),
            'service_status': self.service_status.id
        }
        form = SoldierForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_leave_form_validation(self):
        """Test leave form validation"""
        from core.forms import LeaveForm
        
        soldier = Soldier.objects.create(
            first_name="تست",
            last_name="سرباز",
            national_code="1111111111",
            dispatch_type="training",
            service_start_date=timezone.now().date() - timedelta(days=100),
            birth_date=timezone.now().date() - timedelta(days=8000),
            service_status=self.service_status
        )
        
        form_data = {
            'soldier': soldier.id,
            'leave_type': 'medical',
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=5)
        }
        form = LeaveForm(data=form_data)
        self.assertTrue(form.is_valid())
