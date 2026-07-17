from django.db import models

from employee.models import Employee


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "Present", "Present"
        ABSENT = "Absent", "Absent"
        CHECKED_IN = "Checked In", "Checked In"
        CHECKED_OUT = "Checked Out", "Checked Out"
        LATE = "Late", "Late"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendances")
    check_in = models.DateTimeField(blank=True, null=True)
    check_out = models.DateTimeField(blank=True, null=True)
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CHECKED_IN, db_index=True)

    class Meta:
        ordering = ["-date", "-check_in"]
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.employee.name} - {self.date} ({self.status})"
