from django.urls import path

from . import views

app_name = "cotizaciones"

urlpatterns = [
    # /cotizaciones/ ahora redirige a /negocios/ (pipeline unificado).
    path("", views.redirect_tablero, name="tablero"),
    path("tablero/", views.redirect_tablero, name="tablero_legacy"),
    path("bandeja/", views.bandeja, name="bandeja"),
    path("bandeja/<int:pk>/abrir/", views.abrir_conversacion, name="abrir_conversacion"),
    path("bandeja/<int:pk>/mensajes/", views.enviar_mensaje_whatsapp, name="enviar_mensaje_whatsapp"),
    path("registro/", views.list, name="list"),
    path("nueva/", views.create, name="create"),
    path("<int:pk>/estado/", views.update_estado, name="update_estado"),
    path("oportunidades/<int:pk>/etapa/", views.mover_oportunidad, name="mover_oportunidad"),
]
