from django.urls import path

from . import views

app_name = "seguimientos"

urlpatterns = [
    path("", views.listado, name="listado"),
    path("nuevo/", views.crear, name="crear"),
    path("<int:pk>/cumplir/", views.marcar_cumplido, name="marcar_cumplido"),
]
