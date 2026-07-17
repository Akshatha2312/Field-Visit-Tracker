from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Employee(models.Model):
    class Role(models.TextChoices):
        EMPLOYEE = "Employee", "Employee"
        ADMIN = "Admin", "Admin"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.BigIntegerField(blank=True, null=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)

    class Meta:
        ordering = ["name"]
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def __str__(self):
        return self.name


@receiver(post_save, sender=Employee)
def log_employee_activity(sender, instance, created, **kwargs):
    from dashboard.models import ActivityLog

    if created:
        ActivityLog.objects.create(
            employee=instance,
            activity_type=ActivityLog.ActivityType.EMPLOYEE_CREATED,
            title="Employee Created",
            description=f"{instance.name} was added to the system.",
        )
    else:
        ActivityLog.objects.create(
            employee=instance,
            activity_type=ActivityLog.ActivityType.EMPLOYEE_UPDATED,
            title="Employee Updated",
            description=f"{instance.name}'s profile was updated.",
        )
