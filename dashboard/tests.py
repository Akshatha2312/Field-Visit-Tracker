from datetime import date

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from attendance.models import Attendance
from employee.models import Employee
from visits.models import ClientVisit


class HomePageTests(TestCase):
    def test_home_page_renders_successfully(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Field Visit Tracker')
        self.assertContains(response, 'Employee Visit Management System')


class LoginFlowTests(TestCase):
    def test_invalid_login_shows_error(self):
        response = self.client.post('/login/', {'username': 'wrong', 'password': 'badpass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct')

    def test_admin_login_redirects_to_admin_dashboard(self):
        User = get_user_model()
        user = User.objects.create_user(username='admin', password='strongpass123')
        Employee.objects.create(
            user=user,
            name='Admin User',
            email='admin@example.com',
            password='secret123',
            role=Employee.Role.ADMIN,
        )

        response = self.client.post('/login/', {'username': 'admin', 'password': 'strongpass123'})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admin_dashboard'))

    def test_employee_login_redirects_to_employee_dashboard(self):
        User = get_user_model()
        user = User.objects.create_user(username='employee', password='strongpass123')
        Employee.objects.create(
            user=user,
            name='Employee User',
            email='employee@example.com',
            password='secret123',
            role=Employee.Role.EMPLOYEE,
        )

        response = self.client.post('/login/', {'username': 'employee', 'password': 'strongpass123'})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('employee_dashboard'))

    def test_employee_dashboard_uses_dashboard_template(self):
        User = get_user_model()
        user = User.objects.create_user(username='employee-dashboard-user', password='strongpass123')
        Employee.objects.create(
            user=user,
            name='Employee Dashboard User',
            email='employee-dashboard@example.com',
            password='secret123',
            role=Employee.Role.EMPLOYEE,
        )
        self.client.login(username='employee-dashboard-user', password='strongpass123')

        response = self.client.get(reverse('employee_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertContains(response, 'Welcome back')
        self.assertNotContains(response, "Today's Status")

    def test_authenticated_user_can_access_dashboard(self):
        User = get_user_model()
        user = User.objects.create_user(username='admin', password='strongpass123')
        Employee.objects.create(
            user=user,
            name='Admin User',
            email='admin@example.com',
            password='secret123',
            role=Employee.Role.ADMIN,
        )
        self.client.login(username='admin', password='strongpass123')

        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')

    def test_admin_dashboard_shows_admin_panel_sidebar(self):
        User = get_user_model()
        user = User.objects.create_user(username='paneladmin', password='strongpass123')
        Employee.objects.create(
            user=user,
            name='Panel Admin',
            email='paneladmin@example.com',
            password='secret123',
            role=Employee.Role.ADMIN,
        )
        self.client.login(username='paneladmin', password='strongpass123')

        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Panel')
        self.assertNotContains(response, 'Employee Panel')

    def test_admin_dashboard_keeps_monitoring_widgets_and_removes_quick_notes(self):
        User = get_user_model()
        user = User.objects.create_user(username='admindashboard', password='strongpass123')
        Employee.objects.create(
            user=user,
            name='Admin Dashboard',
            email='admindashboard@example.com',
            password='secret123',
            role=Employee.Role.ADMIN,
        )
        self.client.login(username='admindashboard', password='strongpass123')

        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recent Activity')
        self.assertContains(response, 'Attendance Overview')
        self.assertNotContains(response, 'Quick Notes')

    def test_employee_dashboard_removes_activity_and_chart_widgets(self):
        User = get_user_model()
        user = User.objects.create_user(username='employeedashboard', password='strongpass123')
        Employee.objects.create(
            user=user,
            name='Employee Dashboard',
            email='employeedashboard@example.com',
            password='secret123',
            role=Employee.Role.EMPLOYEE,
        )
        self.client.login(username='employeedashboard', password='strongpass123')

        response = self.client.get(reverse('employee_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Recent Activity')
        self.assertNotContains(response, 'Quick Notes')
        self.assertNotContains(response, 'Attendance Overview')


class AnalyticsDataTests(TestCase):
    def test_analytics_endpoint_returns_summary_and_employee_reports(self):
        User = get_user_model()
        user = User.objects.create_user(username='analyst', password='strongpass123')
        employee = Employee.objects.create(
            user=user,
            name='Analyst Employee',
            email='analyst@example.com',
            password='secret123',
            role=Employee.Role.ADMIN,
        )
        Attendance.objects.create(employee=employee, date=date.today(), status=Attendance.Status.PRESENT)
        ClientVisit.objects.create(
            employee=employee,
            client_name='Ada',
            company_name='Acme',
            contact_number='1234567890',
            location='Lagos',
            visit_date=date.today(),
            purpose='Review',
            status=ClientVisit.Status.COMPLETED,
        )
        self.client.login(username='analyst', password='strongpass123')

        response = self.client.get(reverse('analytics_data'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('summary', payload)
        self.assertIn('employee_reports', payload)
        self.assertEqual(payload['summary']['today_visits'], 1)
        self.assertEqual(payload['employee_reports'][0]['total_visits'], 1)


class PasswordResetTests(TestCase):
    def test_password_reset_page_sends_email(self):
        User = get_user_model()
        User.objects.create_user(username='employee', email='employee@example.com', password='strongpass123')

        response = self.client.get(reverse('password_reset'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Forgot Password')

        response = self.client.post(reverse('password_reset'), {'email': 'employee@example.com'})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password reset', mail.outbox[0].subject)


class RoleBasedAccessTests(TestCase):
    def test_admin_dashboard_attendance_link_points_to_management_page(self):
        User = get_user_model()
        user = User.objects.create_user(username='adminnav', password='strongpass123')
        Employee.objects.create(
            user=user,
            name='Admin Nav',
            email='adminnav@example.com',
            password='secret123',
            role=Employee.Role.ADMIN,
        )

        self.client.login(username='adminnav', password='strongpass123')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Attendance Management')
        self.assertContains(response, f'href="{reverse("attendance:management")}"')

    def test_employee_dashboard_attendance_link_points_to_my_attendance(self):
        User = get_user_model()
        user = User.objects.create_user(username='employeenav', password='strongpass123')
        Employee.objects.create(
            user=user,
            name='Employee Nav',
            email='employeenav@example.com',
            password='secret123',
            role=Employee.Role.EMPLOYEE,
        )

        self.client.login(username='employeenav', password='strongpass123')
        response = self.client.get(reverse('employee_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Attendance')
        self.assertContains(response, f'href="{reverse("attendance:dashboard")}"')

    def test_admin_user_can_access_employee_listing(self):
        User = get_user_model()
        user = User.objects.create_user(username='adminuser', password='strongpass123')
        Employee.objects.create(
            user=user,
            name='Admin User',
            email='admin@example.com',
            password='secret123',
            role=Employee.Role.ADMIN,
        )

        self.client.login(username='adminuser', password='strongpass123')
        response = self.client.get(reverse('employee:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Employees')

    def test_employee_user_is_denied_access_to_admin_listing(self):
        User = get_user_model()
        user = User.objects.create_user(username='employeeuser', password='strongpass123')
        Employee.objects.create(
            user=user,
            name='Employee User',
            email='employee@example.com',
            password='secret123',
            role=Employee.Role.EMPLOYEE,
        )

        self.client.login(username='employeeuser', password='strongpass123')
        response = self.client.get(reverse('employee:list'))

        self.assertEqual(response.status_code, 403)
