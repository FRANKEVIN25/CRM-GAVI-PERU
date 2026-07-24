from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("redirigir/", views.RedireccionPorRolView.as_view(), name="redirigir"),
    path("agentes/", views.ListaAgentesView.as_view(), name="agentes"),
    path("agentes/nuevo/", views.CrearAgenteView.as_view(), name="crear_agente"),
]
