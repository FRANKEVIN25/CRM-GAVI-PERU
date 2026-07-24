from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from whatsapp.models import Conversacion

from .models import Etapa, Oportunidad


@login_required
def negocios(request):
    """
    Vista principal del pipeline comercial — equivalente a "Negocios" en HubSpot.
    Muestra todas las oportunidades del pipeline activo en formato Kanban.

    ?vista=mis → filtra solo las oportunidades del usuario en sesión.
    Por defecto muestra todas (vista de equipo).
    """
    vista = request.GET.get("vista", "todos")

    oportunidades_qs = Oportunidad.objects.select_related(
        "lead", "lead__cliente", "etapa_actual", "pipeline"
    ).prefetch_related("cotizaciones")

    if vista == "mis":
        oportunidades_qs = oportunidades_qs.filter(creado_por=request.user)

    etapas = Etapa.objects.filter(pipeline__activo=True).select_related("pipeline")

    return render(request, "oportunidades/negocios.html", {
        "oportunidades": oportunidades_qs,
        "etapas": etapas,
        "conversaciones_nuevas": Conversacion.objects.filter(
            estado=Conversacion.Estado.NUEVA
        ).count(),
        "vista_actual": vista,
    })
