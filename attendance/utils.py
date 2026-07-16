from django.conf import settings
from django.core.mail import send_mail


def send_checkin_email(employee, attendance):
    if not employee or not attendance or not employee.email:
        return

    subject = "Check In Successful"
    message = (
        f"Hello {employee.name},\n\n"
        f"Your check-in was recorded successfully.\n\n"
        f"Check-in date: {attendance.check_in.date().strftime('%Y-%m-%d')}\n"
        f"Check-in time: {attendance.check_in.strftime('%H:%M:%S')}\n\n"
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

    subject = "Check Out Successful"
    message = (
        f"Hello {employee.name},\n\n"
        f"Your check-out was recorded successfully.\n\n"
        f"Check-out date: {attendance.check_out.date().strftime('%Y-%m-%d')}\n"
        f"Check-out time: {attendance.check_out.strftime('%H:%M:%S')}\n\n"
        "Regards,\n"
        "Field Visit Tracker"
    )

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [employee.email], fail_silently=False)
    except Exception as e:
        print("EMAIL ERROR:", e)
