from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from visits.models import ClientVisit
from visits.utils import send_visit_reminder_email


class Command(BaseCommand):
    help = "Send reminder emails for upcoming client visits scheduled for today."

    def get_sent_log_path(self):
        path = getattr(settings, "VISIT_REMINDER_LOG_PATH", None)
        if path:
            return Path(path)
        return Path(settings.BASE_DIR) / ".visit_reminder_sent"

    def get_sent_visit_ids(self, today):
        sent_file = self.get_sent_log_path()
        if not sent_file.exists():
            return set()

        sent_ids = set()
        with sent_file.open("r", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split(",")
                if len(parts) != 2:
                    continue
                date_str, visit_id = parts
                if date_str == today.isoformat():
                    sent_ids.add(int(visit_id))
        return sent_ids

    def mark_visit_sent(self, visit_id, today):
        sent_file = self.get_sent_log_path()
        sent_file.parent.mkdir(parents=True, exist_ok=True)
        with sent_file.open("a", encoding="utf-8") as file:
            file.write(f"{today.isoformat()},{visit_id}\n")

    def handle(self, *args, **options):
        today = timezone.localdate()
        sent_ids = self.get_sent_visit_ids(today)
        visits = ClientVisit.objects.filter(
            visit_date=today,
            status=ClientVisit.Status.PENDING,
        ).select_related("employee")

        sent_count = 0
        for visit in visits:
            if visit.id in sent_ids:
                continue
            if not visit.employee or not visit.employee.email:
                continue

            send_visit_reminder_email(visit.employee, visit)
            self.mark_visit_sent(visit.id, today)
            sent_count += 1

        if sent_count == 0:
            self.stdout.write(self.style.SUCCESS("No visit reminders to send today."))
            return

        self.stdout.write(self.style.SUCCESS(f"Sent {sent_count} visit reminder(s)."))
