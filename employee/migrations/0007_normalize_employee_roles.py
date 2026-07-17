from django.db import migrations


def normalize_employee_roles(apps, schema_editor):
    Employee = apps.get_model("employee", "Employee")

    for employee in Employee.objects.all():
        raw_role = employee.role
        if raw_role is None:
            new_role = "EMPLOYEE"
        else:
            role_value = str(raw_role).strip()
            normalized = role_value.lower()
            if normalized == "admin":
                new_role = "ADMIN"
            elif normalized == "employee":
                new_role = "EMPLOYEE"
            elif role_value == "":
                new_role = "EMPLOYEE"
            else:
                new_role = role_value

        Employee.objects.filter(pk=employee.pk).update(role=new_role)


class Migration(migrations.Migration):
    dependencies = [
        ("employee", "0006_convert_employee_roles"),
    ]

    operations = [
        migrations.RunPython(normalize_employee_roles, migrations.RunPython.noop),
    ]
