from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from rest_framework.generics import ListAPIView, RetrieveAPIView

from dashboard.models import ActivityLog
from employee.permissions import get_scoped_queryset
from employee.utils import get_employee_for_user

from .forms import ClientVisitForm
from .models import ClientVisit
from .serializers import ClientVisitSerializer
from .utils import send_visit_completed_email, send_visit_created_email, send_visit_reminder_email


@login_required(login_url="login")
def visit_list(request):
    queryset = get_scoped_queryset(request.user, ClientVisit.objects.all())

    search_query = request.GET.get("q", "").strip()
    client_name_filter = request.GET.get("client_name", "").strip()
    company_filter = request.GET.get("company", "").strip()
    location_filter = request.GET.get("location", "").strip()
    employee_filter = request.GET.get("employee", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search_query:
        queryset = queryset.filter(
            Q(client_name__icontains=search_query)
            | Q(company_name__icontains=search_query)
            | Q(location__icontains=search_query)
            | Q(employee__name__icontains=search_query)
        )

    if client_name_filter:
        queryset = queryset.filter(client_name__icontains=client_name_filter)

    if company_filter:
        queryset = queryset.filter(company_name__icontains=company_filter)

    if location_filter:
        queryset = queryset.filter(location__icontains=location_filter)

    if employee_filter:
        queryset = queryset.filter(employee__name__icontains=employee_filter)

    if status_filter:
        queryset = queryset.filter(status=status_filter)

    visits_list = queryset.select_related("employee").order_by("-visit_date", "-created_at")
    paginator = Paginator(visits_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    today = timezone.localdate()

    return render(
        request,
        "visits/list.html",
        {
            "visits": page_obj.object_list,
            "page_obj": page_obj,
            "search_query": search_query,
            "client_name_filter": client_name_filter,
            "company_filter": company_filter,
            "location_filter": location_filter,
            "employee_filter": employee_filter,
            "status_filter": status_filter,
            "today": today,
        },
    )


class ClientVisitListView(ListAPIView):
    queryset = ClientVisit.objects.select_related("employee").order_by("-visit_date", "-created_at")
    serializer_class = ClientVisitSerializer

    def get_queryset(self):
        return get_scoped_queryset(
            self.request.user,
            self.queryset,
            employee_field="employee__user",
        )


class ClientVisitDetailView(RetrieveAPIView):
    queryset = ClientVisit.objects.select_related("employee").order_by("-visit_date", "-created_at")
    serializer_class = ClientVisitSerializer

    def get_queryset(self):
        return get_scoped_queryset(
            self.request.user,
            self.queryset,
            employee_field="employee__user",
        )


@login_required(login_url="login")
def visit_create(request):
    employee = get_employee_for_user(request.user)
    if employee is None:
        messages.error(request, "No employee profile is linked to your account.")
        return redirect("visits:list")

    if request.method == "POST":
        form = ClientVisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.employee = employee
            visit.save()
            ActivityLog.objects.create(
                employee=employee,
                activity_type=ActivityLog.ActivityType.VISIT_CREATED,
                title="Visit Created",
                description=f"{employee.name} created a visit for {visit.client_name}.",
            )
            send_visit_created_email(employee, visit)
            messages.success(request, "Client visit added successfully.")
            return redirect("visits:list")
    else:
        form = ClientVisitForm()

    return render(request, "visits/form.html", {"form": form, "title": "Add Client Visit"})


@login_required(login_url="login")
def visit_edit(request, pk):
    employee = get_employee_for_user(request.user)
    visit = get_object_or_404(ClientVisit, pk=pk, employee=employee)

    if request.method == "POST":
        form = ClientVisitForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            messages.success(request, "Client visit updated successfully.")
            return redirect("visits:list")
    else:
        form = ClientVisitForm(instance=visit)

    return render(request, "visits/form.html", {"form": form, "title": "Edit Client Visit"})


@login_required(login_url="login")
def visit_delete(request, pk):
    employee = get_employee_for_user(request.user)
    visit = get_object_or_404(ClientVisit, pk=pk, employee=employee)

    if request.method == "POST":
        visit.delete()
        messages.success(request, "Client visit deleted successfully.")
        return redirect("visits:list")

    return render(request, "visits/delete_confirm.html", {"visit": visit})


@login_required(login_url="login")
def mark_completed(request, pk):
    employee = get_employee_for_user(request.user)
    visit = get_object_or_404(ClientVisit, pk=pk, employee=employee)
    visit.status = ClientVisit.Status.COMPLETED
    visit.save(update_fields=["status"])
    ActivityLog.objects.create(
        employee=employee,
        activity_type=ActivityLog.ActivityType.VISIT_COMPLETED,
        title="Visit Completed",
        description=f"{employee.name} completed the visit for {visit.client_name}.",
    )
    send_visit_completed_email(employee, visit)
    messages.success(request, "Visit marked as completed.")
    return redirect("visits:list")


@login_required(login_url="login")
def visit_detail(request, pk):
    employee = get_employee_for_user(request.user)
    visit = get_object_or_404(ClientVisit, pk=pk, employee=employee)
    today = timezone.localdate()
    timeline_steps = [
        {"label": "Visit Created", "status": "complete"},
        {"label": "Accepted", "status": "active" if visit.status == ClientVisit.Status.PENDING else "complete"},
        {"label": "In Progress", "status": "active" if visit.status == ClientVisit.Status.PENDING else "complete"},
        {"label": "Completed", "status": "active" if visit.status == ClientVisit.Status.COMPLETED else "pending"},
    ]
    return render(request, "visits/detail.html", {"visit": visit, "timeline_steps": timeline_steps, "today": today})


@login_required(login_url="login")
def visit_reports(request):
    queryset = get_scoped_queryset(request.user, ClientVisit.objects.all())

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    date_filter = request.GET.get("date", "").strip()

    if search_query:
        queryset = queryset.filter(Q(client_name__icontains=search_query) | Q(company_name__icontains=search_query))
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if date_filter:
        queryset = queryset.filter(visit_date=date_filter)

    visits = queryset.order_by("-visit_date", "-created_at")
    today = timezone.localdate()
    month_start = today.replace(day=1)

    # Use aggregate to get all counts in a single query instead of multiple .count() calls
    summary_aggs = queryset.aggregate(
        total_visits=Count('id'),
        pending_visits=Count('id', filter=Q(status=ClientVisit.Status.PENDING)),
        completed_visits=Count('id', filter=Q(status=ClientVisit.Status.COMPLETED)),
        visits_this_month=Count('id', filter=Q(visit_date__gte=month_start, visit_date__lte=today)),
    )
    
    summary = {
        "total_visits": summary_aggs['total_visits'],
        "pending_visits": summary_aggs['pending_visits'],
        "completed_visits": summary_aggs['completed_visits'],
        "visits_this_month": summary_aggs['visits_this_month'],
    }

    return render(
        request,
        "visits/reports.html",
        {
            "visits": visits,
            "summary": summary,
            "search_query": search_query,
            "status_filter": status_filter,
            "date_filter": date_filter,
        },
    )


@login_required(login_url="login")
def send_visit_reminder(request, pk):
    employee = get_employee_for_user(request.user)
    visit = get_object_or_404(ClientVisit, pk=pk, employee=employee)

    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)

    # Check if visit is eligible for reminder
    is_upcoming = visit.visit_date >= today
    is_tomorrow = visit.visit_date == tomorrow
    is_pending = visit.status == ClientVisit.Status.PENDING

    if not (is_upcoming and is_pending):
        messages.error(request, "Reminders can only be sent for upcoming and pending visits.")
        return redirect("visits:detail", pk=pk)

    # Send reminder email
    send_visit_reminder_email(employee, visit)
    messages.success(request, "Reminder email sent successfully.")
    return redirect("visits:detail", pk=pk)
