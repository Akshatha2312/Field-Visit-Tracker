from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from employee.models import Employee

from .models import Attendance


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
