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

    def test_admin_can_access_any_visit_detail(self):
        admin_user = get_user_model().objects.create_user(username="adminvisit", password="secret123")
        admin_employee = Employee.objects.create(
            name="Admin Visit",
            email="adminvisit@example.com",
            password="secret123",
            role=Employee.Role.ADMIN,
            user=admin_user,
        )
        visit = ClientVisit.objects.create(
            employee=self.employee,
            client_name="Other Employee Visit",
            company_name="Acme",
            contact_number="555-0100",
            location="Lagos",
            visit_date=date(2026, 7, 16),
            purpose="Review",
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse("visits:detail", kwargs={"pk": visit.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Other Employee Visit")

    def test_employee_cannot_access_other_employee_visit_detail(self):
        other_employee = Employee.objects.create(
            name="Jamie",
            email="jamie@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
        )
        visit = ClientVisit.objects.create(
            employee=other_employee,
            client_name="Other Employee Visit",
            company_name="Acme",
            contact_number="555-0100",
            location="Lagos",
            visit_date=date(2026, 7, 16),
            purpose="Review",
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("visits:detail", kwargs={"pk": visit.pk}))

        self.assertEqual(response.status_code, 302)
