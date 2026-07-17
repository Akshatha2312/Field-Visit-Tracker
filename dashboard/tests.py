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

    def test_authenticated_user_can_access_dashboard(self):
        User = get_user_model()
        user = User.objects.create_user(username='employee', password='strongpass123')
        self.client.login(username='employee', password='strongpass123')

        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')


class AnalyticsDataTests(TestCase):
    def test_analytics_endpoint_returns_summary_and_employee_reports(self):
        User = get_user_model()
        user = User.objects.create_user(username='analyst', password='strongpass123')
        employee = Employee.objects.create(
            user=user,
            name='Analyst Employee',
            email='analyst@example.com',
            password='secret123',
            role=Employee.Role.EMPLOYEE,
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
