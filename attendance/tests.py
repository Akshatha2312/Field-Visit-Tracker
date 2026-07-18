from datetime import date, datetime, timezone as dt_timezone
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse

from employee.models import Employee

from .models import Attendance
from .utils import send_checkin_email, send_checkout_email


class AttendanceModelTests(TestCase):
    def test_attendance_string_representation(self):
        employee = Employee.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
        )
        attendance = Attendance.objects.create(
            employee=employee,
            date=date(2026, 7, 16),
            status=Attendance.Status.PRESENT,
        )

        self.assertEqual(str(attendance), "Jane Doe - 2026-07-16 (Present)")


class AttendanceViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="jane",
            email="jane@example.com",
            password="secret123",
        )
        self.employee = Employee.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
            user=self.user,
        )

    def test_check_in_creates_today_attendance(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("attendance:check_in"))

        self.assertEqual(response.status_code, 302)
        attendance = Attendance.objects.get(employee=self.employee)
        self.assertEqual(attendance.status, Attendance.Status.CHECKED_IN)

    def test_duplicate_check_in_is_blocked_same_day(self):
        self.client.force_login(self.user)
        self.client.post(reverse("attendance:check_in"))

        response = self.client.post(reverse("attendance:check_in"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Attendance.objects.filter(employee=self.employee).count(), 1)

    def test_check_in_rejects_non_today_date(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("attendance:check_in"), {"date": "2026-07-16"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Attendance.objects.filter(employee=self.employee).count(), 0)

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("Attendance can only be recorded for today.", messages)

    def test_check_out_rejects_non_today_date(self):
        self.client.force_login(self.user)
        self.client.post(reverse("attendance:check_in"))

        response = self.client.post(reverse("attendance:check_out"), {"date": "2026-07-16"})

        self.assertEqual(response.status_code, 302)
        attendance = Attendance.objects.get(employee=self.employee)
        self.assertIsNone(attendance.check_out)

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("Attendance can only be recorded for today.", messages)

    def test_check_out_updates_existing_attendance(self):
        self.client.force_login(self.user)
        self.client.post(reverse("attendance:check_in"))

        response = self.client.post(reverse("attendance:check_out"))

        self.assertEqual(response.status_code, 302)
        attendance = Attendance.objects.get(employee=self.employee)
        self.assertIsNotNone(attendance.check_out)
        self.assertEqual(attendance.status, Attendance.Status.CHECKED_OUT)

    def test_admin_can_view_attendance_management(self):
        admin_user = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="secret123",
        )
        Employee.objects.create(
            name="Admin User",
            email="adminuser@example.com",
            password="secret123",
            role=Employee.Role.ADMIN,
            user=admin_user,
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("attendance:management"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "attendance/management.html")

    def test_employee_is_redirected_from_attendance_management(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("attendance:management"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("attendance:dashboard"))


class AttendanceEmailTests(TestCase):
    def setUp(self):
        self.employee = Employee.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
        )

    @patch("attendance.utils.send_mail")
    def test_check_in_email_uses_ist_display_time(self, mock_send_mail):
        attendance = Attendance(
            employee=self.employee,
            date=date(2026, 7, 18),
            check_in=datetime(2026, 7, 18, 0, 0, tzinfo=dt_timezone.utc),
            status=Attendance.Status.CHECKED_IN,
        )

        send_checkin_email(self.employee, attendance)

        subject, message, from_email, recipient_list = mock_send_mail.call_args.args
        self.assertEqual(subject, "Check In Successful")
        self.assertIn("Check-in date: 2026-07-18", message)
        self.assertIn("Check-in time: 05:30:00", message)
        self.assertEqual(from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(recipient_list, [self.employee.email])

    @patch("attendance.utils.send_mail")
    def test_check_out_email_uses_ist_display_time(self, mock_send_mail):
        attendance = Attendance(
            employee=self.employee,
            date=date(2026, 7, 18),
            check_out=datetime(2026, 7, 18, 12, 0, tzinfo=dt_timezone.utc),
            status=Attendance.Status.CHECKED_OUT,
        )

        send_checkout_email(self.employee, attendance)

        subject, message, from_email, recipient_list = mock_send_mail.call_args.args
        self.assertEqual(subject, "Check Out Successful")
        self.assertIn("Check-out date: 2026-07-18", message)
        self.assertIn("Check-out time: 17:30:00", message)
        self.assertEqual(from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(recipient_list, [self.employee.email])
