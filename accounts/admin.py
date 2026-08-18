from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-created_at"]
    list_display = ["nickname", "email", "name", "plan", "is_active", "is_staff"]
    search_fields = ["nickname", "email", "name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("email", "nickname", "password")}),
        ("Perfil", {"fields": ("name", "birth_date", "sex", "height", "plan")}),
        (
            "Permissões",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Termos", {"fields": ("terms_accepted", "terms_accepted_at")}),
        ("Datas", {"fields": ("id", "created_at", "updated_at", "last_login")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nickname",
                    "name",
                    "birth_date",
                    "sex",
                    "height",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
