from django.urls import path

from . import views

app_name = "cotizaciones"

urlpatterns = [
    # Cotizaciones abre directamente el espacio de trabajo diario. El
    # registro completo sigue disponible como una vista secundaria.
    path("", views.tablero, name="tablero"),
    # Compatibilidad con enlaces, marcadores y pestañas abiertas antes de
    # que el tablero se convirtiera en la ruta principal.
    path("tablero/", views.tablero, name="tablero_legacy"),
    path("registro/", views.list, name="list"),
    path("nueva/", views.create, name="create"),
    path("<int:pk>/estado/", views.update_estado, name="update_estado"),
]
