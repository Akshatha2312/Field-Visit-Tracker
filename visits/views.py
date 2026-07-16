from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from rest_framework.generics import ListAPIView, RetrieveAPIView

from employee.models import Employee

from .forms import ClientVisitForm
from .models import ClientVisit
from .serializers import ClientVisitSerializer
from .utils import send_visit_completed_email, send_visit_created_email


def get_employee_for_user(user):
    if hasattr(user, "employee"):
        return user.employee

    return Employee.objects.filter(email=user.email).first() or Employee.objects.filter(name=user.username).first()


@login_required(login_url="login")
def visit_list(request):
    employee = get_employee_for_user(request.user)
    queryset = ClientVisit.objects.none()
    if employee is not None:
        queryset = ClientVisit.objects.filter(employee=employee)

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
        },
    )


class ClientVisitListView(ListAPIView):
    queryset = ClientVisit.objects.select_related("employee").order_by("-visit_date", "-created_at")
    serializer_class = ClientVisitSerializer


class ClientVisitDetailView(RetrieveAPIView):
    queryset = ClientVisit.objects.select_related("employee").order_by("-visit_date", "-created_at")
    serializer_class = ClientVisitSerializer


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
    send_visit_completed_email(employee, visit)
    messages.success(request, "Visit marked as completed.")
    return redirect("visits:list")


@login_required(login_url="login")
def visit_reports(request):
    employee = get_employee_for_user(request.user)
    queryset = ClientVisit.objects.none()
    if employee is not None:
        queryset = ClientVisit.objects.filter(employee=employee)

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

    summary = {
        "total_visits": queryset.count(),
        "pending_visits": queryset.filter(status=ClientVisit.Status.PENDING).count(),
        "completed_visits": queryset.filter(status=ClientVisit.Status.COMPLETED).count(),
        "visits_this_month": queryset.filter(visit_date__gte=month_start, visit_date__lte=today).count(),
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
