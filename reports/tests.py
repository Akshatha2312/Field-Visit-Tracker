from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from attendance.models import Attendance
from employee.models import Employee
from visits.models import ClientVisit


class ReportsAccessTests(TestCase):
    def test_admin_reports_page_shows_employee_filter_and_full_exports(self):
        admin_user = get_user_model().objects.create_user(username="adminreports", email="adminreports@example.com", password="secret123")
        Employee.objects.create(
            user=admin_user,
            name="Admin Report User",
            email="adminreportuser@example.com",
            password="secret123",
            role=Employee.Role.ADMIN,
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse("reports:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reports")
        self.assertContains(response, 'name="employee"')
        self.assertContains(response, "Download PDF")
        self.assertContains(response, "Download Excel")
        self.assertContains(response, "Download CSV")

    def test_employee_reports_page_uses_my_reports_and_hides_employee_filter(self):
        user = get_user_model().objects.create_user(username="employeereports", email="employeereports@example.com", password="secret123")
        employee = Employee.objects.create(user=user, name="Carol", email="carol@example.com", password="secret123")
        Attendance.objects.create(employee=employee, date="2024-01-10", status=Attendance.Status.PRESENT)
        ClientVisit.objects.create(
            employee=employee,
            client_name="John Doe",
            company_name="Acme",
            visit_date="2024-01-10",
            location="Nairobi",
            status=ClientVisit.Status.PENDING,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("reports:dashboard"), {"from_date": "2024-01-01", "to_date": "2024-01-31"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Reports")
        self.assertNotContains(response, 'name="employee"')
        self.assertContains(response, "Download PDF")
        self.assertContains(response, "Download Excel")
        self.assertContains(response, "Download CSV")

    def test_employee_reports_only_include_their_own_data(self):
        user = get_user_model().objects.create_user(username="reporter", email="reporter@example.com", password="secret123")
        employee = Employee.objects.create(user=user, name="Alice", email="alice@example.com", password="secret123")
        Attendance.objects.create(employee=employee, date="2024-01-10", status=Attendance.Status.PRESENT)
        ClientVisit.objects.create(
            employee=employee,
            client_name="John Doe",
            company_name="Acme",
            visit_date="2024-01-10",
            location="Nairobi",
            status=ClientVisit.Status.PENDING,
        )

        other_employee = Employee.objects.create(name="Bob", email="bob@example.com", password="secret123")
        Attendance.objects.create(employee=other_employee, date="2024-01-11", status=Attendance.Status.ABSENT)
        ClientVisit.objects.create(
            employee=other_employee,
            client_name="Jane Doe",
            company_name="Beta",
            visit_date="2024-01-11",
            location="Nairobi",
            status=ClientVisit.Status.COMPLETED,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("reports:dashboard"), {"from_date": "2024-01-01", "to_date": "2024-01-31"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertNotContains(response, "Jane Doe")

    def test_reports_page_displays_pagination_controls_when_many_results_exist(self):
        user = get_user_model().objects.create_user(username="reporter_pagination", email="reporter_pagination@example.com", password="secret123")
        employee = Employee.objects.create(user=user, name="Alice Pagination", email="alice-pagination@example.com", password="secret123")

        for index in range(11):
            ClientVisit.objects.create(
                employee=employee,
                client_name=f"Visit {index}",
                company_name="Acme",
                visit_date="2024-01-10",
                location="Nairobi",
                status=ClientVisit.Status.PENDING,
            )

        self.client.force_login(user)
        response = self.client.get(reverse("reports:dashboard"), {"from_date": "2024-01-01", "to_date": "2024-01-31"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Previous")
        self.assertContains(response, "Next")
        self.assertContains(response, "Page 1")
        self.assertContains(response, "Page 2")


class ReportsPdfExportTests(TestCase):
    def test_download_pdf_returns_pdf_response(self):
        user = get_user_model().objects.create_user(username="reporter", email="reporter@example.com", password="secret123")
        employee = Employee.objects.create(user=user, name="Alice", email="alice@example.com", password="secret123")
        Attendance.objects.create(employee=employee, date="2024-01-10", status=Attendance.Status.PRESENT)
        ClientVisit.objects.create(
            employee=employee,
            client_name="John Doe",
            company_name="Acme",
            visit_date="2024-01-10",
            location="Nairobi",
            status=ClientVisit.Status.PENDING,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("reports:download_pdf"), {"from_date": "2024-01-01", "to_date": "2024-01-31"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_download_excel_returns_excel_response(self):
        user = get_user_model().objects.create_user(username="reporter2", email="reporter2@example.com", password="secret123")
        employee = Employee.objects.create(user=user, name="Bob", email="bob@example.com", password="secret123")
        Attendance.objects.create(employee=employee, date="2024-01-11", status=Attendance.Status.PRESENT)
        ClientVisit.objects.create(
            employee=employee,
            client_name="Jane Doe",
            company_name="Beta",
            visit_date="2024-01-11",
            location="Nairobi",
            status=ClientVisit.Status.COMPLETED,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("reports:download_excel"), {"from_date": "2024-01-01", "to_date": "2024-01-31"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
