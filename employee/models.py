from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Employee(models.Model):
    class Role(models.TextChoices):
        EMPLOYEE = "EMPLOYEE", "Employee"
        ADMIN = "ADMIN", "Admin"

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
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_default=Role.EMPLOYEE,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def __str__(self):
        return self.name

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN


@receiver(post_save, sender=Employee)
def sync_employee_role_and_log_activity(sender, instance, created, **kwargs):
    from dashboard.models import ActivityLog

    if instance.user_id is not None and instance.user is not None:
        instance.user.is_staff = instance.is_admin
        instance.user.save(update_fields=["is_staff"])

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
