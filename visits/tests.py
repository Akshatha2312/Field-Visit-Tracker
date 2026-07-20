from datetime import date
import tempfile
import uuid
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

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


class ClientVisitReminderCommandTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="alexr", password="secret123")
        self.employee = Employee.objects.create(
            name="Alex Smith",
            email="alex@example.com",
            password="secret123",
            role=Employee.Role.EMPLOYEE,
            user=self.user,
        )

    def test_send_visit_reminders_command_sends_email_for_today_pending_visit(self):
        visit = ClientVisit.objects.create(
            employee=self.employee,
            client_name="Ada Lovelace",
            company_name="Acme",
            contact_number="555-0100",
            location="Lagos",
            visit_date=timezone.localdate(),
            purpose="Review",
        )

        temp_path = Path(tempfile.gettempdir()) / f"visit_reminder_{uuid.uuid4().hex}.log"
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
            VISIT_REMINDER_LOG_PATH=str(temp_path),
        ):
            call_command("send_visit_reminders")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Reminder: Upcoming Client Visit")
        self.assertIn("Client Name: Ada Lovelace", mail.outbox[0].body)

    def test_send_visit_reminders_command_does_not_send_for_past_or_completed_visits(self):
        ClientVisit.objects.create(
            employee=self.employee,
            client_name="Past Client",
            company_name="Acme",
            contact_number="555-0100",
            location="Lagos",
            visit_date=date(2020, 1, 1),
            purpose="Review",
            status=ClientVisit.Status.PENDING,
        )
        ClientVisit.objects.create(
            employee=self.employee,
            client_name="Completed Client",
            company_name="Acme",
            contact_number="555-0100",
            location="Lagos",
            visit_date=timezone.localdate(),
            purpose="Review",
            status=ClientVisit.Status.COMPLETED,
        )

        temp_path = Path(tempfile.gettempdir()) / f"visit_reminder_{uuid.uuid4().hex}.log"
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
            VISIT_REMINDER_LOG_PATH=str(temp_path),
        ):
            call_command("send_visit_reminders")

        self.assertEqual(len(mail.outbox), 0)
