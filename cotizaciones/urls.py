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
    path("bandeja/", views.bandeja, name="bandeja"),
    path("bandeja/<int:pk>/abrir/", views.abrir_conversacion, name="abrir_conversacion"),
    path("bandeja/<int:pk>/mensajes/", views.enviar_mensaje_whatsapp, name="enviar_mensaje_whatsapp"),
    path("registro/", views.list, name="list"),
    path("nueva/", views.create, name="create"),
    path("<int:pk>/estado/", views.update_estado, name="update_estado"),
    path("oportunidades/<int:pk>/etapa/", views.mover_oportunidad, name="mover_oportunidad"),
]
