"""Replica as regras de negócio de MEASUREMENTS_MODULE.md (healthcheck-api)."""

import math
from datetime import date

from .models import CIRCUMFERENCE_FIELDS, SKINFOLD_FIELDS

SKINFOLDS_INCOMPLETE = "SKINFOLDS_INCOMPLETE"


def _age(birth_date):
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def validate_skinfolds(data):
    """`data` é um dict com os 7 campos de dobras (valor ou None).
    Levanta ValueError com missing_fields se for um conjunto parcial."""
    provided = {f: data.get(f) for f in SKINFOLD_FIELDS if data.get(f) is not None}
    if not provided:
        return
    if len(provided) == 7:
        return
    missing = [f for f in SKINFOLD_FIELDS if data.get(f) is None]
    raise SkinfoldsIncompleteError(missing)


class SkinfoldsIncompleteError(ValueError):
    def __init__(self, missing_fields):
        self.missing_fields = missing_fields
        self.error_code = SKINFOLDS_INCOMPLETE
        super().__init__(
            "All 7 skinfold fields must be provided together or none at all."
        )


def calculate_pollock_body_fat(skinfold_sum, age, sex):
    """Jackson & Pollock (1978) homens / Jackson, Pollock & Ward (1980) mulheres."""
    s = float(skinfold_sum)
    a = float(age)
    if sex == "male":
        body_density = 1.112 - 0.00043499 * s + 0.00000055 * (s**2) - 0.00028826 * a
    else:
        body_density = 1.097 - 0.00046971 * s + 0.00000056 * (s**2) - 0.00012828 * a
    return (495 / body_density) - 450


def calculate_navy_body_fat(neck, waist, height, sex, hip=None):
    neck = float(neck)
    waist = float(waist)
    height = float(height)
    if sex == "male":
        value = 495 / (
            1.0324 - 0.19077 * math.log10(waist - neck) + 0.15456 * math.log10(height)
        ) - 450
    else:
        if hip is None:
            return None
        hip = float(hip)
        value = 495 / (
            1.29579
            - 0.35004 * math.log10(waist + hip - neck)
            + 0.221 * math.log10(height)
        ) - 450
    return value


def resolve_body_fat(measurement_data, user):
    """Retorna (body_fat_percentage, method, navy_body_fat_percentage) a partir de um
    dict com os campos do Measurement (dobras, circunferências) e o `user` dono
    (para idade/sexo/altura). Prioridade: Pollock > Navy."""
    sex = user.sex
    age = _age(user.birth_date)
    height = float(user.height)

    skinfolds = {f: measurement_data.get(f) for f in SKINFOLD_FIELDS}
    has_all_skinfolds = all(v is not None for v in skinfolds.values())

    navy_bf = None
    neck = measurement_data.get("neck")
    waist = measurement_data.get("waist")
    hip = measurement_data.get("hip")
    if neck is not None and waist is not None:
        if sex == "male":
            navy_bf = calculate_navy_body_fat(neck, waist, height, sex)
        elif hip is not None:
            navy_bf = calculate_navy_body_fat(neck, waist, height, sex, hip=hip)

    if has_all_skinfolds:
        skinfold_sum = sum(float(v) for v in skinfolds.values())
        pollock_bf = calculate_pollock_body_fat(skinfold_sum, age, sex)
        return round(pollock_bf, 2), "pollock", (round(navy_bf, 2) if navy_bf is not None else None)

    if navy_bf is not None:
        return round(navy_bf, 2), "navy", round(navy_bf, 2)

    return None, None, None


def calculate_lean_fat_mass(weight, body_fat_percentage):
    if body_fat_percentage is None:
        return None, None
    weight = float(weight)
    bf = float(body_fat_percentage)
    lean_mass = weight * (1 - bf / 100)
    fat_mass = weight * (bf / 100)
    return round(lean_mass, 2), round(fat_mass, 2)


def calculate_waist_hip_ratio(waist, hip, sex):
    if waist is None or hip is None:
        return None
    ratio = round(float(waist) / float(hip), 2)

    risk = None
    if sex == "male":
        if ratio < 0.90:
            risk = "low"
        elif ratio <= 0.99:
            risk = "moderate"
        else:
            risk = "high"
    elif sex == "female":
        if ratio < 0.80:
            risk = "low"
        elif ratio <= 0.85:
            risk = "moderate"
        else:
            risk = "high"

    return {"value": ratio, "risk": risk}


def apply_calculations(measurement, user):
    """Preenche os campos calculados de `measurement` (não salva)."""
    data = {f: getattr(measurement, f) for f in SKINFOLD_FIELDS + CIRCUMFERENCE_FIELDS}
    bf, method, navy_bf = resolve_body_fat(data, user)
    measurement.body_fat_percentage = bf
    measurement.body_fat_method = method
    measurement.navy_body_fat_percentage = navy_bf
    lean_mass, fat_mass = calculate_lean_fat_mass(measurement.weight, bf)
    measurement.lean_mass = lean_mass
    measurement.fat_mass = fat_mass
