"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/accounts/login/", permanent=False)),
    path("admin/", admin.site.urls),
    path("usuarios/", include("usuarios.urls")),
    # Rutas de la app de clientes (búsqueda / ficha / creación)
    path("clientes/", include("clientes.urls")),
    # Rutas de la app de cotizaciones (lista, filtros, cambio de estado,
    # y el tablero Kanban -- incluye la interfaz de WhatsApp consolidada,
    # ver cotizaciones/templatetags/cotizaciones_tags.py)
    path("cotizaciones/", include("cotizaciones.urls")),

    # Pipeline comercial: vista Kanban de Oportunidades (Negocios).
    path("negocios/", include("oportunidades.urls")),

    # Gestión de tareas comerciales del equipo.
    path("tareas/", include("tareas.urls")),

    # Solo webhooks de proveedor; la interfaz sigue consolidada en cotizaciones.
    path("webhooks/whatsapp/", include("whatsapp.urls")),
    # Esto solo (una línea) ya trae login, logout, cambio de contraseña
    # y recuperación de contraseña -- todo construido por Django, ver FEAT-00
    path("accounts/", include("django.contrib.auth.urls")),
]
