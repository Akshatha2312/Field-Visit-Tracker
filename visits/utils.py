from django.conf import settings
from django.core.mail import send_mail


def send_visit_created_email(employee, visit):
    if not employee or not visit or not employee.email:
        return

    subject = "Visit Created"
    message = (
        f"Hello {employee.name},\n\n"
        f"A client visit has been created successfully.\n\n"
        f"Client Name: {visit.client_name}\n"
        f"Company Name: {visit.company_name}\n"
        f"Visit Date: {visit.visit_date}\n"
        f"Location: {visit.location}\n"
        f"Status: {visit.status}\n\n"
        "Regards,\n"
        "Field Visit Tracker"
    )

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [employee.email], fail_silently=False)
    except Exception:
        pass


def send_visit_completed_email(employee, visit):
    if not employee or not visit or not employee.email:
        return

    subject = "Visit Completed"
    message = (
        f"Hello {employee.name},\n\n"
        f"The client visit has been marked as completed.\n\n"
        f"Client Name: {visit.client_name}\n"
        f"Company Name: {visit.company_name}\n"
        f"Completion Status: {visit.status}\n\n"
        "Regards,\n"
        "Field Visit Tracker"
    )

    try:
        print("COMPLETED EMAIL FUNCTION CALLED")
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [employee.email], fail_silently=False)
    except Exception as e:
        print("EMAIL ERROR:", e)
