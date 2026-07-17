from django.urls import path
from . import views

app_name = "clientes"

urlpatterns = [
    path("", views.search, name="search"),
    path("new/", views.create, name="create"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/interacciones/add/", views.add_interaccion, name="add_interaccion"),
]
