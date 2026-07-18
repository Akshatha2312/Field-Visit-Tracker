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

    def test_employee_defaults_to_employee_role(self):
        employee = Employee.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            password="secret123",
        )

        self.assertEqual(employee.role, Employee.Role.EMPLOYEE)
        self.assertFalse(employee.is_admin)


class EmployeeManagementViewTests(TestCase):
    def _create_admin_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="admin_emp", password="strongpass123")
        Employee.objects.create(
            user=user,
            name="Admin Employee",
            email="admin-emp@example.com",
            password="secret123",
            role=Employee.Role.ADMIN,
        )
        return user

    def _create_employee_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="regular_emp", password="strongpass123")
        Employee.objects.create(
            user=user,
            name="Regular Employee",
            email="regular-emp@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
        )
        return user

    def test_admin_can_create_employee(self):
        self._create_admin_user()
        self.client.login(username="admin_emp", password="strongpass123")

        response = self.client.post(
            reverse("employee:create"),
            {
                "username": "newemployee",
                "name": "New Employee",
                "email": "newemployee@example.com",
                "phone_number": "9876543210",
                "role": Employee.Role.EMPLOYEE,
                "password": "newpass123",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Employee.objects.filter(email="newemployee@example.com").exists())
        self.assertTrue(get_user_model().objects.filter(username="newemployee").exists())

    def test_admin_can_edit_employee(self):
        self._create_admin_user()
        self.client.login(username="admin_emp", password="strongpass123")
        employee = Employee.objects.create(
            name="Old Name",
            email="old@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
        )

        response = self.client.post(
            reverse("employee:edit", args=[employee.pk]),
            {
                "username": "updatedemployee",
                "name": "Updated Name",
                "email": "updated@example.com",
                "phone_number": "1234567890",
                "role": Employee.Role.ADMIN,
                "password": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        employee.refresh_from_db()
        self.assertEqual(employee.name, "Updated Name")
        self.assertEqual(employee.email, "updated@example.com")
        self.assertEqual(employee.role, Employee.Role.ADMIN)

    def test_admin_can_delete_employee(self):
        self._create_admin_user()
        self.client.login(username="admin_emp", password="strongpass123")
        employee = Employee.objects.create(
            name="Delete Me",
            email="delete-me@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
        )

        response = self.client.post(reverse("employee:delete", args=[employee.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Employee.objects.filter(pk=employee.pk).exists())

    def test_admin_can_view_employee_details(self):
        self._create_admin_user()
        self.client.login(username="admin_emp", password="strongpass123")
        employee = Employee.objects.create(
            name="Detail View",
            email="detail-view@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
        )

        response = self.client.get(reverse("employee:detail", args=[employee.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detail View")

    def test_employee_user_is_denied_employee_management(self):
        self._create_employee_user()
        self.client.login(username="regular_emp", password="strongpass123")

        response = self.client.get(reverse("employee:list"))

        self.assertEqual(response.status_code, 403)

    def test_employee_list_page_displays_pagination_when_more_than_page_size(self):
        self._create_admin_user()
        self.client.login(username="admin_emp", password="strongpass123")

        for index in range(11):
            Employee.objects.create(
                name=f"Employee {index}",
                email=f"employee{index}@example.com",
                password="secret123",
                role=Employee.Role.EMPLOYEE,
            )

        response = self.client.get(reverse("employee:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Previous")
        self.assertContains(response, "Next")
        self.assertContains(response, "Page 1")
        self.assertContains(response, "Page 2")


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
