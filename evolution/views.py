import json

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from measurements.models import CIRCUMFERENCE_FIELDS, CIRCUMFERENCE_LABELS, Measurement, SKINFOLD_FIELDS, SKINFOLD_LABELS

from . import services


DEFAULT_RANGE = "weeks-12"


def _parse_range(request):
    """Lê o parâmetro `range` (ex.: 'weeks-12', 'count-5', 'all') e retorna os
    kwargs prontos para `services.get_summary`, junto com o valor normalizado
    (pra manter o <select> marcado certo no template)."""
    raw = request.GET.get("range", DEFAULT_RANGE)

    if raw == "all":
        return {"limit": None}, "all"

    mode, _, value = raw.partition("-")
    try:
        value = int(value)
    except (TypeError, ValueError):
        mode, value = "weeks", 12

    if mode == "count":
        return {"last_n": value, "limit": None}, f"count-{value}"

    return {"weeks": value, "limit": None}, f"weeks-{value}"


def _chart_context(user, range_kwargs, range_value):
    points = services.get_summary(user, **range_kwargs)
    return {
        "dates": json.dumps([p["date"].isoformat() for p in points]),
        "weights": json.dumps([p["weight"] for p in points]),
        "body_fat": json.dumps([p["body_fat_percentage"] for p in points]),
        "lean_mass": json.dumps([p["lean_mass"] for p in points]),
        "fat_mass": json.dumps([p["fat_mass"] for p in points]),
        "whr": json.dumps([p["waist_hip_ratio"] for p in points]),
        "range_value": range_value,
    }


@login_required
def index_view(request):
    range_kwargs, range_value = _parse_range(request)
    latest = services.get_latest(request.user)
    context = _chart_context(request.user, range_kwargs, range_value)
    context["latest"] = latest
    return render(request, "evolution/index.html", context)


@login_required
def summary_partial_view(request):
    """Endpoint HTMX: re-renderiza só os gráficos ao trocar o filtro de período."""
    range_kwargs, range_value = _parse_range(request)
    context = _chart_context(request.user, range_kwargs, range_value)
    return render(request, "evolution/_charts.html", context)


@login_required
def compare_view(request):
    from_id = request.GET.get("from")
    to_id = request.GET.get("to")
    result = None
    skinfold_rows = []
    circumference_rows = []
    if from_id and to_id:
        m_from = get_object_or_404(Measurement, pk=from_id, user=request.user)
        m_to = get_object_or_404(Measurement, pk=to_id, user=request.user)
        result = services.get_compare(request.user, m_from, m_to)

        skinfold_rows = [
            {
                "label": SKINFOLD_LABELS[f],
                "from": getattr(m_from, f),
                "to": getattr(m_to, f),
                "diff": result["skinfolds"][f],
            }
            for f in SKINFOLD_FIELDS
        ]
        circumference_rows = [
            {
                "label": CIRCUMFERENCE_LABELS[f],
                "from": getattr(m_from, f),
                "to": getattr(m_to, f),
                "diff": result["circumferences"][f],
            }
            for f in CIRCUMFERENCE_FIELDS
        ]

    measurements = request.user.measurements.order_by("-measurement_date")
    return render(
        request,
        "evolution/compare.html",
        {
            "measurements": measurements,
            "result": result,
            "from_id": from_id,
            "to_id": to_id,
            "skinfold_rows": skinfold_rows,
            "circumference_rows": circumference_rows,
        },
    )


@login_required
def delta_partial_view(request, measurement_id):
    measurement = get_object_or_404(Measurement, pk=measurement_id, user=request.user)
    result = services.get_delta(request.user, measurement)
    return render(request, "evolution/_delta.html", {"result": result})
