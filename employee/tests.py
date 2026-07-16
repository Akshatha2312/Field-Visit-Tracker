from datetime import date

from django.test import TestCase

from .models import Employee


class EmployeeModelTests(TestCase):
    def test_employee_string_representation(self):
        employee = Employee.objects.create(
            name="John Doe",
            email="john@example.com",
            password="secret123",
            role=Employee.Role.ADMIN,
        )

        self.assertEqual(str(employee), "John Doe")
