from django.db import models

from employee.models import Employee


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "Present", "Present"
        ABSENT = "Absent", "Absent"
        LATE = "Late", "Late"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendances")
    check_in = models.DateTimeField(blank=True, null=True)
    check_out = models.DateTimeField(blank=True, null=True)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)

    class Meta:
        ordering = ["-date", "-check_in"]

    def __str__(self):
        return f"{self.employee.name} - {self.date} ({self.status})"
