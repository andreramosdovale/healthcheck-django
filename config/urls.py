from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("measurements/", include("measurements.urls")),
    path("evolution/", include("evolution.urls")),
]
