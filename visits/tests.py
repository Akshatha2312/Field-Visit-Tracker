from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from employee.models import Employee

from .models import ClientVisit


class ClientVisitModelTests(TestCase):
    def test_client_visit_string_representation(self):
        employee = Employee.objects.create(
            name="Alex Smith",
            email="alex@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
        )
        visit = ClientVisit.objects.create(
            employee=employee,
            client_name="Maria Gomez",
            company_name="Northwind",
            contact_number="555-0100",
            location="Lagos",
            visit_date=date(2026, 7, 16),
            purpose="Project review",
            status=ClientVisit.Status.PENDING,
        )

        self.assertEqual(str(visit), "Maria Gomez - Northwind")


class ClientVisitViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="alex", password="secret123")
        self.employee = Employee.objects.create(
            name="Alex Smith",
            email="alex@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
            user=self.user,
        )

    def test_list_view_shows_employee_visits(self):
        self.client.force_login(self.user)
        ClientVisit.objects.create(
            employee=self.employee,
            client_name="Ada Lovelace",
            company_name="Acme",
            contact_number="555-0100",
            location="Lagos",
            visit_date=date(2026, 7, 16),
            purpose="Review",
        )

        response = self.client.get(reverse("visits:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ada Lovelace")
