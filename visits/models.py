from django.db import models

from employee.models import Employee


class ClientVisit(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        COMPLETED = "Completed", "Completed"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="client_visits")
    client_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    visit_date = models.DateField(db_index=True)
    purpose = models.TextField()
    meeting_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-visit_date", "-created_at"]
        indexes = [
            models.Index(fields=['employee', 'visit_date']),
            models.Index(fields=['employee', 'status']),
        ]

    def __str__(self):
        return f"{self.client_name} - {self.company_name}"
