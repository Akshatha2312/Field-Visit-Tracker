from django.db import migrations


def normalize_employee_roles(apps, schema_editor):
    Employee = apps.get_model("employee", "Employee")
    Employee.objects.filter(role="Employee").update(role="EMPLOYEE")
    Employee.objects.filter(role="Admin").update(role="ADMIN")
    Employee.objects.filter(role="").update(role="EMPLOYEE")
    Employee.objects.filter(role__isnull=True).update(role="EMPLOYEE")


class Migration(migrations.Migration):

    dependencies = [
        ("employee", "0005_alter_employee_role"),
    ]

    operations = [
        migrations.RunPython(normalize_employee_roles, migrations.RunPython.noop),
    ]
