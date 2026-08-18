from django.contrib import admin

from .models import Measurement


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ["user", "measurement_date", "weight", "body_fat_percentage", "body_fat_method"]
    list_filter = ["body_fat_method"]
    search_fields = ["user__nickname", "user__email"]
    readonly_fields = [
        "id",
        "body_fat_percentage",
        "body_fat_method",
        "navy_body_fat_percentage",
        "lean_mass",
        "fat_mass",
        "created_at",
        "updated_at",
    ]
