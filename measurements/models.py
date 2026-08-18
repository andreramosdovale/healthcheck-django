import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

SKINFOLD_FIELDS = [
    "triceps",
    "subscapular",
    "chest",
    "midaxillary",
    "suprailiac",
    "abdominal",
    "thigh",
]

CIRCUMFERENCE_FIELDS = [
    "neck",
    "waist",
    "abdomen",
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


def skinfold_field(**kwargs):
    return models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        **kwargs,
    )


def circumference_field(**kwargs):
    return models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(200)],
        **kwargs,
    )


class Measurement(models.Model):
    class BodyFatMethod(models.TextChoices):
        POLLOCK = "pollock", "Pollock 7-dobras"
        NAVY = "navy", "Navy"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="measurements"
    )
    measurement_date = models.DateField()
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(20), MaxValueValidator(500)],
    )

    # Skinfolds (mm, 1-100) — all-or-nothing, enforced in services.validate_skinfolds
    triceps = skinfold_field()
    subscapular = skinfold_field()
    chest = skinfold_field()
    midaxillary = skinfold_field()
    suprailiac = skinfold_field()
    abdominal = skinfold_field()
    thigh = skinfold_field()

    # Circumferences (cm, 10-200) — independent
    neck = circumference_field()
    waist = circumference_field()
    abdomen = circumference_field()
    hip = circumference_field()
    shoulders = circumference_field()
    chest_circ = circumference_field()
    left_thigh = circumference_field()
    right_thigh = circumference_field()
    left_calf = circumference_field()
    right_calf = circumference_field()
    left_bicep_relaxed = circumference_field()
    right_bicep_relaxed = circumference_field()
    left_bicep_flexed = circumference_field()
    right_bicep_flexed = circumference_field()

    # Calculated (never accepted as input — always derived in services.py)
    body_fat_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    body_fat_method = models.CharField(
        max_length=7, choices=BodyFatMethod.choices, null=True, blank=True
    )
    navy_body_fat_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    lean_mass = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fat_mass = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ["-measurement_date"]

    def __str__(self):
        return f"{self.user.nickname} - {self.measurement_date}"

    @property
    def lean_mass_percentage(self):
        if self.body_fat_percentage is None:
            return None
        return round(100 - float(self.body_fat_percentage), 2)

    @property
    def waist_hip_ratio(self):
        from .services import calculate_waist_hip_ratio

        return calculate_waist_hip_ratio(self.waist, self.hip, self.user.sex if self.user_id else None)
