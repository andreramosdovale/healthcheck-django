from django import forms
from django.core.exceptions import ValidationError

from config.tailwind_forms import TailwindFormMixin

from .models import CIRCUMFERENCE_FIELDS, SKINFOLD_FIELDS, Measurement
from .services import SkinfoldsIncompleteError, validate_skinfolds


class MeasurementForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Measurement
        fields = ["measurement_date", "weight"] + SKINFOLD_FIELDS + CIRCUMFERENCE_FIELDS
        widgets = {"measurement_date": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned_data = super().clean()
        skinfold_data = {f: cleaned_data.get(f) for f in SKINFOLD_FIELDS}
        try:
            validate_skinfolds(skinfold_data)
        except SkinfoldsIncompleteError as exc:
            raise ValidationError(
                f"{exc} (faltando: {', '.join(exc.missing_fields)})", code=exc.error_code
            )
        return cleaned_data


class MeasurementFilterForm(TailwindFormMixin, forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
