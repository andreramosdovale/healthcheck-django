from django.urls import path

from . import views

app_name = "measurements"

urlpatterns = [
    path("", views.list_view, name="list"),
    path("new/", views.create_view, name="create"),
    path("<uuid:pk>/", views.detail_view, name="detail"),
    path("<uuid:pk>/edit/", views.edit_view, name="edit"),
    path("<uuid:pk>/delete/", views.delete_view, name="delete"),
]
