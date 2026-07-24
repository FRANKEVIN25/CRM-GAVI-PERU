from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from .models import Tarea
from .services import completar_tarea


@login_required
def lista(request):
    # Actualiza estados antes de mostrar para que las vencidas ya aparezcan como VENCIDA.
    Tarea.objects.marcar_vencidas()

    vista = request.GET.get("vista", "todas")
    estado = request.GET.get("estado", "")
    tipo = request.GET.get("tipo", "")
    prioridad = request.GET.get("prioridad", "")

    tareas_qs = Tarea.objects.select_related(
        "asignada_a__usuario", "creada_por__usuario", "content_type"
    )

    if vista == "mis":
        agente = getattr(request.user, "agente", None)
        tareas_qs = tareas_qs.filter(asignada_a=agente) if agente else tareas_qs.none()

    if estado:
        tareas_qs = tareas_qs.filter(estado=estado)
    if tipo:
        tareas_qs = tareas_qs.filter(tipo=tipo)
    if prioridad:
        tareas_qs = tareas_qs.filter(prioridad=prioridad)

    # Precarga los objetos asociados (Lead u Oportunidad) para evitar N+1.
    # prefetch_related no funciona directamente con GenericFK, así que
    # resolvemos el objeto en Python y lo adjuntamos a cada tarea.
    tareas_lista = list(tareas_qs)
    for tarea in tareas_lista:
        tarea.objeto_resuelto = tarea.objeto  # una sola consulta por tipo gracias al select_related del ct

    base_qs = Tarea.objects.all()
    if vista == "mis":
        agente = getattr(request.user, "agente", None)
        base_qs = base_qs.filter(asignada_a=agente) if agente else base_qs.none()

    return render(request, "tareas/lista.html", {
        "tareas": tareas_lista,
        "conteos": {
            "total": base_qs.count(),
            "pendientes": base_qs.filter(estado=Tarea.Estado.PENDIENTE).count(),
            "vencidas": base_qs.filter(estado=Tarea.Estado.VENCIDA).count(),
            "completadas": base_qs.filter(estado=Tarea.Estado.COMPLETADA).count(),
        },
        "tipos": Tarea.Tipo.choices,
        "prioridades": Tarea.Prioridad.choices,
        "estados": Tarea.Estado.choices,
        "estado_actual": estado,
        "tipo_actual": tipo,
        "prioridad_actual": prioridad,
        "vista_actual": vista,
    })


@login_required
def completar(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    tarea = get_object_or_404(Tarea, pk=pk)
    agente = getattr(request.user, "agente", None)
    try:
        completar_tarea(tarea, agente=agente)
    except ValidationError:
        pass  # Ya estaba completada; ignorar y redirigir.
    return redirect("tareas:lista")

