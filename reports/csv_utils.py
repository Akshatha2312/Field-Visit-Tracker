import csv
from io import StringIO

from django.http import HttpResponse


def build_csv_response(context):
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Field Visit Tracker Report"])
    writer.writerow([])
    writer.writerow(["Generated Date", context.get("generated_at", "")])
    writer.writerow(["Applied Filters", ""])
    writer.writerow(["From Date", context.get("from_date") or "All"])
    writer.writerow(["To Date", context.get("to_date") or "All"])
    writer.writerow(["Employee", context.get("employee_name") or "All"])
    writer.writerow(["Visit Status", context.get("visit_status") or "All"])
    writer.writerow([])
    writer.writerow(["Summary", ""])
    writer.writerow(["Total Attendance Records", context.get("total_attendance_records", 0)])
    writer.writerow(["Total Present", context.get("total_present", 0)])
    writer.writerow(["Total Client Visits", context.get("total_client_visits", 0)])
    writer.writerow(["Pending Visits", context.get("pending_visits", 0)])
    writer.writerow(["Completed Visits", context.get("completed_visits", 0)])
    writer.writerow([])

    visits = context.get("visits", [])
    if visits:
        writer.writerow(["Visit Details", ""])
        writer.writerow(["Employee", "Client Name", "Company Name", "Visit Date", "Status"])
        for visit in visits:
            writer.writerow(
                [
                    visit.employee.name if visit.employee else "-",
                    visit.client_name,
                    visit.company_name,
                    str(visit.visit_date),
                    visit.status,
                ]
            )
    else:
        writer.writerow(["Visit Details", ""])
        writer.writerow(["No records found."])

    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="field_visit_tracker_report.csv"'
    return response
