from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


def _format_ist_date_time(value):
    localized_value = timezone.localtime(value)
    return localized_value.strftime('%Y-%m-%d'), localized_value.strftime('%H:%M:%S')


def send_checkin_email(employee, attendance):
    if not employee or not attendance or not employee.email:
        return

    check_in_date, check_in_time = _format_ist_date_time(attendance.check_in)

    subject = "Check In Successful"
    message = (
        f"Hello {employee.name},\n\n"
        f"Your check-in was recorded successfully.\n\n"
        f"Check-in date: {check_in_date}\n"
        f"Check-in time: {check_in_time}\n\n"
        "Regards,\n"
        "Field Visit Tracker"
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [employee.email],
            fail_silently=False,
        )
    except Exception as e:
        print("EMAIL ERROR:", e)


def send_checkout_email(employee, attendance):
    if not employee or not attendance or not employee.email:
        return

    check_out_date, check_out_time = _format_ist_date_time(attendance.check_out)

    subject = "Check Out Successful"
    message = (
        f"Hello {employee.name},\n\n"
        f"Your check-out was recorded successfully.\n\n"
        f"Check-out date: {check_out_date}\n"
        f"Check-out time: {check_out_time}\n\n"
        "Regards,\n"
        "Field Visit Tracker"
    )

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [employee.email], fail_silently=False)
    except Exception as e:
        print("EMAIL ERROR:", e)
