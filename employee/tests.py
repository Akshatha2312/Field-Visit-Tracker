from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Employee


class EmployeeModelTests(TestCase):
    def test_employee_string_representation(self):
        employee = Employee.objects.create(
            name="John Doe",
            email="john@example.com",
            password="secret123",
            role=Employee.Role.ADMIN,
            phone_number=9876543210,
        )

        self.assertEqual(str(employee), "John Doe")
        self.assertEqual(employee.phone_number, 9876543210)


class ProfileViewTests(TestCase):
    def test_profile_update_saves_name_email_and_phone_and_shows_success_message(self):
        User = get_user_model()
        user = User.objects.create_user(username="employee", email="old@example.com", password="strongpass123")
        employee = Employee.objects.create(
            user=user,
            name="Old Name",
            email="old@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
        )
        self.client.login(username="employee", password="strongpass123")

        response = self.client.post(
            reverse("employee:profile"),
            {
                "name": "New Name",
                "email": "new@example.com",
                "phone_number": "9876543210",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        employee.refresh_from_db()
        self.assertEqual(employee.name, "New Name")
        self.assertEqual(employee.email, "new@example.com")
        self.assertEqual(employee.phone_number, 9876543210)
        self.assertContains(response, "updated successfully")

    def test_profile_rejects_invalid_email(self):
        User = get_user_model()
        user = User.objects.create_user(username="employee2", email="old2@example.com", password="strongpass123")
        Employee.objects.create(
            user=user,
            name="Old Name",
            email="old2@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
        )
        self.client.login(username="employee2", password="strongpass123")

        response = self.client.post(
            reverse("employee:profile"),
            {
                "name": "Name",
                "email": "not-an-email",
                "phone_number": "1234567890",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address")
