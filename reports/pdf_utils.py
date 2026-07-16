from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf_response(context):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=24,
        textColor=colors.HexColor("#1f4e79"),
        spaceAfter=0.2 * inch,
    )
    heading_style = ParagraphStyle(
        name="HeadingStyle",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2f4f4f"),
        spaceAfter=0.1 * inch,
    )
    normal_style = styles["BodyText"]

    story = []
    story.append(Paragraph("Field Visit Tracker Report", title_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(f"Generated Date: {timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Applied Filters", heading_style))
    story.append(Paragraph(f"From Date: {context.get('from_date') or 'All'}", normal_style))
    story.append(Paragraph(f"To Date: {context.get('to_date') or 'All'}", normal_style))
    story.append(Paragraph(f"Employee: {context.get('employee_name') or 'All'}", normal_style))
    story.append(Paragraph(f"Visit Status: {context.get('visit_status') or 'All'}", normal_style))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Summary", heading_style))
    summary_data = [
        ["Total Attendance Records", str(context.get("total_attendance_records", 0))],
        ["Total Present", str(context.get("total_present", 0))],
        ["Total Client Visits", str(context.get("total_client_visits", 0))],
        ["Pending Visits", str(context.get("pending_visits", 0))],
        ["Completed Visits", str(context.get("completed_visits", 0))],
    ]
    summary_table = Table(summary_data, colWidths=[3 * inch, 1.5 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f9fc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9dee8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9f2ff")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Visit Details", heading_style))
    visits = context.get("visits", [])
    if visits:
        table_rows = [["Employee", "Client Name", "Company Name", "Visit Date", "Status"]]
        for visit in visits:
            table_rows.append(
                [
                    visit.employee.name if visit.employee else "-",
                    visit.client_name,
                    visit.company_name,
                    str(visit.visit_date),
                    visit.status,
                ]
            )
        details_table = Table(table_rows, repeatRows=1, colWidths=[1.1 * inch, 1.2 * inch, 1.2 * inch, 1.0 * inch, 0.9 * inch])
        details_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9f2ff")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9dee8")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ]
            )
        )
        story.append(details_table)
    else:
        story.append(Paragraph("No records found.", normal_style))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="field_visit_tracker_report.pdf"'
    return response
