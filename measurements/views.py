from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import MeasurementFilterForm, MeasurementForm
from .models import Measurement
from .services import apply_calculations


@login_required
def list_view(request):
    qs = Measurement.objects.filter(user=request.user)

    filter_form = MeasurementFilterForm(request.GET or None)
    if filter_form.is_valid():
        date_from = filter_form.cleaned_data.get("date_from")
        date_to = filter_form.cleaned_data.get("date_to")
        if date_from:
            qs = qs.filter(measurement_date__gte=date_from)
        if date_to:
            qs = qs.filter(measurement_date__lte=date_to)

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "measurements/list.html",
        {"page_obj": page_obj, "filter_form": filter_form},
    )


@login_required
def create_view(request):
    if request.method == "POST":
        form = MeasurementForm(request.POST)
        if form.is_valid():
            measurement = form.save(commit=False)
            measurement.user = request.user
            apply_calculations(measurement, request.user)
            measurement.save()
            messages.success(request, "Medição registrada.")
            return redirect("measurements:detail", pk=measurement.pk)
    else:
        form = MeasurementForm()

    return render(request, "measurements/form.html", {"form": form, "mode": "create"})


@login_required
def detail_view(request, pk):
    measurement = get_object_or_404(Measurement, pk=pk, user=request.user)
    return render(request, "measurements/detail.html", {"measurement": measurement})


@login_required
def edit_view(request, pk):
    measurement = get_object_or_404(Measurement, pk=pk, user=request.user)

    if request.method == "POST":
        form = MeasurementForm(request.POST, instance=measurement)
        if form.is_valid():
            measurement = form.save(commit=False)
            apply_calculations(measurement, request.user)
            measurement.save()
            messages.success(request, "Medição atualizada.")
            return redirect("measurements:detail", pk=measurement.pk)
    else:
        form = MeasurementForm(instance=measurement)

    return render(
        request, "measurements/form.html", {"form": form, "mode": "edit", "measurement": measurement}
    )


@login_required
@require_http_methods(["POST"])
def delete_view(request, pk):
    measurement = get_object_or_404(Measurement, pk=pk, user=request.user)
    measurement.delete()
    messages.success(request, "Medição excluída.")
    return redirect("measurements:list")
