from django.db import models

from employee.models import Employee


class ActivityLog(models.Model):
    class ActivityType(models.TextChoices):
        EMPLOYEE_CREATED = "Employee Created", "Employee Created"
        EMPLOYEE_UPDATED = "Employee Updated", "Employee Updated"
        CHECK_IN = "Check In", "Check In"
        CHECK_OUT = "Check Out", "Check Out"
        VISIT_CREATED = "Visit Created", "Visit Created"
        VISIT_COMPLETED = "Visit Completed", "Visit Completed"
        REPORT_GENERATED = "Report Generated", "Report Generated"

    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="activity_logs")
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.created_at}"

    @property
    def badge_class(self):
        classes = {
            self.ActivityType.EMPLOYEE_CREATED: "bg-primary",
            self.ActivityType.EMPLOYEE_UPDATED: "bg-info",
            self.ActivityType.CHECK_IN: "bg-success",
            self.ActivityType.CHECK_OUT: "bg-warning text-dark",
            self.ActivityType.VISIT_CREATED: "bg-secondary",
            self.ActivityType.VISIT_COMPLETED: "bg-success",
            self.ActivityType.REPORT_GENERATED: "bg-dark",
        }
        return classes.get(self.activity_type, "bg-secondary")

    @property
    def icon_class(self):
        icons = {
            self.ActivityType.EMPLOYEE_CREATED: "bi-person-plus",
            self.ActivityType.EMPLOYEE_UPDATED: "bi-person-gear",
            self.ActivityType.CHECK_IN: "bi-box-arrow-in-right",
            self.ActivityType.CHECK_OUT: "bi-box-arrow-right",
            self.ActivityType.VISIT_CREATED: "bi-geo-alt",
            self.ActivityType.VISIT_COMPLETED: "bi-check2-circle",
            self.ActivityType.REPORT_GENERATED: "bi-file-earmark-bar-graph",
        }
        return icons.get(self.activity_type, "bi-list-task")
