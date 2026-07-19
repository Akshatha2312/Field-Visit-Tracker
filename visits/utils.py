import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


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
        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [employee.email],
            fail_silently=False,
        )
        logger.info("Visit created email sent successfully to %s (result=%s)", employee.email, result)
    except Exception as e:
        logger.exception(
            "Failed to send visit created email for %s. Error: %s",
            employee.email,
            str(e),
        )


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
        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [employee.email],
            fail_silently=False,
        )
        logger.info("Visit completed email sent successfully to %s (result=%s)", employee.email, result)
    except Exception as e:
        logger.exception(
            "Failed to send visit completed email for %s. Error: %s",
            employee.email,
            str(e),
        )


def send_visit_reminder_email(employee, visit):
    if not employee or not visit or not employee.email:
        return

    subject = "Reminder: Upcoming Client Visit"
    message = (
        f"Hello {employee.name},\n\n"
        f"This is a reminder for your upcoming client visit.\n\n"
        f"Employee Name: {employee.name}\n"
        f"Client Name: {visit.client_name}\n"
        f"Company: {visit.company_name}\n"
        f"Visit Date: {visit.visit_date}\n"
        f"Location: {visit.location}\n"
        f"Purpose: {visit.purpose}\n\n"
        "Regards,\n"
        "Field Visit Tracker"
    )

    try:
        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [employee.email],
            fail_silently=False,
        )
        logger.info("Visit reminder email sent successfully to %s (result=%s)", employee.email, result)
    except Exception as e:
        logger.exception(
            "Failed to send visit reminder email for %s. Error: %s",
            employee.email,
            str(e),
        )
