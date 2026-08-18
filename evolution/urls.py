from django.urls import path

from . import views

app_name = "evolution"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("charts/", views.summary_partial_view, name="charts_partial"),
    path("compare/", views.compare_view, name="compare"),
    path("delta/<uuid:measurement_id>/", views.delta_partial_view, name="delta_partial"),
]
