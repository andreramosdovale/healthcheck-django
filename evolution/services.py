"""Replica as regras de negócio de EVOLUTION_MODULE.md (healthcheck-api)."""

from datetime import date, timedelta

from measurements.models import CIRCUMFERENCE_FIELDS, SKINFOLD_FIELDS
from measurements.services import calculate_waist_hip_ratio

STABILITY_THRESHOLDS = {
    "weight": 0.2,
    "body_fat_percentage": 0.2,
    "lean_mass": 0.2,
    "fat_mass": 0.2,
    "triceps": 1.0,
    "subscapular": 1.0,
    "chest": 1.0,
    "midaxillary": 1.0,
    "suprailiac": 1.0,
    "abdominal": 1.0,
    "thigh": 1.0,
    "skinfold_sum": 2.0,
    "whr": 0.01,
    "neck": 0.5,
    "waist": 0.5,
    "hip": 0.5,
    "shoulders": 0.5,
    "chest_circ": 0.5,
    "left_thigh": 0.5,
    "right_thigh": 0.5,
    "left_calf": 0.5,
    "right_calf": 0.5,
    "left_bicep_relaxed": 0.5,
    "right_bicep_relaxed": 0.5,
    "left_bicep_flexed": 0.5,
    "right_bicep_flexed": 0.5,
}

CIRCUMFERENCE_DELTA_FIELDS = [
    "neck",
    "waist",
    "hip",
    "shoulders",
    "chest_circ",
    "left_thigh",
    "right_thigh",
    "left_calf",
    "right_calf",
    "left_bicep_relaxed",
    "right_bicep_relaxed",
    "left_bicep_flexed",
    "right_bicep_flexed",
]


def _f(value):
    return None if value is None else float(value)


def get_summary(user, *, limit=30, date_from=None, date_to=None, weeks=None, last_n=None):
    """Retorna pontos de série temporal ordenados por data ascendente.

    Filtros mutuamente exclusivos (nesta ordem de prioridade): `weeks`
    (janela relativa terminando hoje), `last_n` (últimas N medições,
    independente de data), `date_from`/`date_to`. `limit=None` = sem teto
    (all time) — ainda assim respeita os demais filtros se combinados.
    """
    if limit is not None:
        limit = min(limit, 365)

    qs = user.measurements.all()
    if weeks is not None:
        start = date.today() - timedelta(weeks=weeks)
        qs = qs.filter(measurement_date__gte=start)
    else:
        if date_from:
            qs = qs.filter(measurement_date__gte=date_from)
        if date_to:
            qs = qs.filter(measurement_date__lte=date_to)

    if last_n is not None:
        measurements = list(qs.order_by("-measurement_date")[:last_n])
    elif limit is not None:
        measurements = list(qs.order_by("-measurement_date")[:limit])
    else:
        measurements = list(qs.order_by("-measurement_date"))
    measurements.reverse()  # ascendente para o gráfico

    points = []
    for m in measurements:
        whr = None
        if m.waist is not None and m.hip is not None:
            whr = round(float(m.waist) / float(m.hip), 4)
        points.append(
            {
                "date": m.measurement_date,
                "weight": _f(m.weight),
                "body_fat_percentage": _f(m.body_fat_percentage),
                "body_fat_method": m.body_fat_method,
                "lean_mass": _f(m.lean_mass),
                "fat_mass": _f(m.fat_mass),
                "waist_hip_ratio": whr,
            }
        )
    return points


def _field_diff(m_to, m_from, field, round_to=2):
    a = _f(getattr(m_to, field))
    b = _f(getattr(m_from, field))
    if a is None or b is None:
        return None
    return round(a - b, round_to)


def get_compare(user, measurement_a, measurement_b):
    """`measurement_a`/`measurement_b` já validados como pertencentes ao user.
    Normaliza cronologicamente (from = mais antiga, to = mais recente).
    Compara todos os campos disponíveis: composição, dobras cutâneas
    (individuais + soma) e circunferências — não só peso/%gordura."""
    if measurement_a.measurement_date <= measurement_b.measurement_date:
        m_from, m_to = measurement_a, measurement_b
    else:
        m_from, m_to = measurement_b, measurement_a

    days = (m_to.measurement_date - m_from.measurement_date).days

    diff = {
        "days": days,
        "weight": _field_diff(m_to, m_from, "weight"),
        "body_fat_percentage": _field_diff(m_to, m_from, "body_fat_percentage"),
        "lean_mass": _field_diff(m_to, m_from, "lean_mass"),
        "fat_mass": _field_diff(m_to, m_from, "fat_mass"),
    }

    skinfolds = {}
    skinfold_sum_to = skinfold_sum_from = None
    if all(getattr(m_to, f) is not None for f in SKINFOLD_FIELDS):
        skinfold_sum_to = sum(_f(getattr(m_to, f)) for f in SKINFOLD_FIELDS)
    if all(getattr(m_from, f) is not None for f in SKINFOLD_FIELDS):
        skinfold_sum_from = sum(_f(getattr(m_from, f)) for f in SKINFOLD_FIELDS)
    for f in SKINFOLD_FIELDS:
        skinfolds[f] = _field_diff(m_to, m_from, f)
    skinfolds["sum"] = (
        round(skinfold_sum_to - skinfold_sum_from, 2)
        if skinfold_sum_to is not None and skinfold_sum_from is not None
        else None
    )

    circumferences = {f: _field_diff(m_to, m_from, f) for f in CIRCUMFERENCE_FIELDS}

    whr_to = calculate_waist_hip_ratio(m_to.waist, m_to.hip, user.sex)
    whr_from = calculate_waist_hip_ratio(m_from.waist, m_from.hip, user.sex)
    circumferences["waist_hip_ratio"] = (
        round(whr_to["value"] - whr_from["value"], 2)
        if whr_to and whr_from
        else None
    )

    return {
        "from": m_from,
        "to": m_to,
        "diff": diff,
        "skinfolds": skinfolds,
        "circumferences": circumferences,
    }


def get_latest(user):
    """Retorna (current, previous, trend, trend_code) ou None se não houver medições."""
    measurements = list(user.measurements.order_by("-measurement_date")[:2])
    if not measurements:
        return None

    current = measurements[0]
    previous = measurements[1] if len(measurements) > 1 else None

    if previous is None:
        return {"current": current, "previous": None, "trend": None, "trend_code": "first_measurement"}

    if current.body_fat_percentage is not None and previous.body_fat_percentage is not None:
        diff = _f(current.body_fat_percentage) - _f(previous.body_fat_percentage)
        if diff <= -2:
            trend, code = "improving", "excellent_progress"
        elif diff <= -1:
            trend, code = "improving", "good_progress"
        elif diff >= 1:
            trend, code = "worsening", "fat_increased"
        else:
            trend, code = "stable", "stable_results"
    else:
        diff = _f(current.weight) - _f(previous.weight)
        if diff <= -1:
            trend, code = "improving", "weight_loss"
        elif diff >= 1:
            trend, code = "worsening", "weight_gain"
        else:
            trend, code = "stable", "weight_stable"

    return {"current": current, "previous": previous, "trend": trend, "trend_code": code}


def _direction(current_value, previous_value, threshold):
    if current_value is None or previous_value is None:
        return None
    diff = current_value - previous_value
    if abs(diff) < threshold:
        return "stable"
    return "up" if diff > 0 else "down"


def get_delta(user, measurement):
    """`measurement` já validado como pertencente ao user."""
    previous = (
        user.measurements.filter(measurement_date__lt=measurement.measurement_date)
        .order_by("-measurement_date")
        .first()
    )
    if previous is None:
        return {"measurement_id": measurement.id, "previous_measurement_id": None, "delta": None}

    delta = {}

    for field in ["weight", "body_fat_percentage", "lean_mass", "fat_mass"]:
        delta[field] = _direction(
            _f(getattr(measurement, field)), _f(getattr(previous, field)), STABILITY_THRESHOLDS[field]
        )

    skinfold_sum_current = skinfold_sum_previous = None
    if all(getattr(measurement, f) is not None for f in SKINFOLD_FIELDS):
        skinfold_sum_current = sum(_f(getattr(measurement, f)) for f in SKINFOLD_FIELDS)
    if all(getattr(previous, f) is not None for f in SKINFOLD_FIELDS):
        skinfold_sum_previous = sum(_f(getattr(previous, f)) for f in SKINFOLD_FIELDS)

    for field in SKINFOLD_FIELDS:
        delta[field] = _direction(
            _f(getattr(measurement, field)), _f(getattr(previous, field)), STABILITY_THRESHOLDS[field]
        )
    delta["skinfold_sum"] = _direction(
        skinfold_sum_current, skinfold_sum_previous, STABILITY_THRESHOLDS["skinfold_sum"]
    )

    for field in CIRCUMFERENCE_DELTA_FIELDS:
        delta[field] = _direction(
            _f(getattr(measurement, field)), _f(getattr(previous, field)), STABILITY_THRESHOLDS[field]
        )

    # compositionBalance: soma ponderada de sinais disponíveis
    score = 0
    has_signal = False

    lean_dir = _direction(_f(measurement.lean_mass), _f(previous.lean_mass), STABILITY_THRESHOLDS["lean_mass"])
    if lean_dir is not None and lean_dir != "stable":
        has_signal = True
        score += 2 if lean_dir == "up" else -2

    fat_dir = _direction(_f(measurement.fat_mass), _f(previous.fat_mass), STABILITY_THRESHOLDS["fat_mass"])
    if fat_dir is not None and fat_dir != "stable":
        has_signal = True
        score += -2 if fat_dir == "up" else 2

    skinfold_dir = _direction(
        skinfold_sum_current, skinfold_sum_previous, STABILITY_THRESHOLDS["skinfold_sum"]
    )
    if skinfold_dir is not None and skinfold_dir != "stable":
        has_signal = True
        score += 1  # doc: tanto "down" quanto "up" somam +1 (pontuação da variação, não direção)

    whr_current = whr_previous = None
    if measurement.waist is not None and measurement.hip is not None:
        whr_current = _f(measurement.waist) / _f(measurement.hip)
    if previous.waist is not None and previous.hip is not None:
        whr_previous = _f(previous.waist) / _f(previous.hip)
    whr_dir = _direction(whr_current, whr_previous, STABILITY_THRESHOLDS["whr"])
    if whr_dir is not None and whr_dir != "stable":
        has_signal = True
        score += 1 if whr_dir == "down" else -1

    if not has_signal:
        delta["composition_balance"] = None
    elif score > 0:
        delta["composition_balance"] = "up"
    elif score < 0:
        delta["composition_balance"] = "down"
    else:
        delta["composition_balance"] = "stable"

    return {
        "measurement_id": measurement.id,
        "previous_measurement_id": previous.id,
        "delta": delta,
    }
