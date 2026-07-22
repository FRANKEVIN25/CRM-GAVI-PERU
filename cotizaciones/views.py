from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from clientes.models import Cliente

from .forms import CotizacionForm
from .models import Cotizacion
from .services import reemplazar_cotizacion, transicionar_cotizacion
from oportunidades.models import Etapa, Oportunidad
from oportunidades.services import (
    cerrar_oportunidad_ganada, cerrar_oportunidad_perdida, crear_oportunidad,
    mover_oportunidad_de_etapa,
)
from whatsapp.models import Conversacion, MensajeWhatsApp, Sede


@login_required
def list(request):
    estado = request.GET.get("estado", "")
    vendedor_id = request.GET.get("vendedor", "")

    cotizaciones = Cotizacion.objects.select_related("cliente", "usuario")
    if estado:
        cotizaciones = cotizaciones.filter(estado=estado)
    if vendedor_id:
        cotizaciones = cotizaciones.filter(usuario_id=vendedor_id)

    vendedores = get_user_model().objects.filter(cotizacion__isnull=False).distinct()

    return render(request, "cotizaciones/list.html", {
        "cotizaciones": cotizaciones,
        "estados": Cotizacion.Estado.choices,
        "vendedores": vendedores,
        "estado_actual": estado,
        "vendedor_actual": vendedor_id,
        "form": CotizacionForm(),
    })


# Adonde puede volver create() despues de guardar. Whitelist cerrada (en
# vez de confiar en la URL que mande el POST) para no abrir un open-redirect.
_DESTINOS_CREATE = {
    "list": "cotizaciones:list",
    "tablero": "cotizaciones:tablero",
    "bandeja": "cotizaciones:bandeja",
}


@login_required
def create(request):
    if request.method == "POST":
        form = CotizacionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                cotizacion = form.save(commit=False)
                cotizacion.usuario = request.user
                conversacion = None
                conversacion_id = request.POST.get("conversacion_id")
                if conversacion_id:
                    conversacion = Conversacion.objects.select_for_update().filter(pk=conversacion_id).first()
                oportunidad = conversacion.oportunidad_actual if conversacion and conversacion.cliente_id == cotizacion.cliente_id else None
                if oportunidad is None:
                    oportunidad = crear_oportunidad(cliente=cotizacion.cliente, usuario=request.user)
                cotizacion.oportunidad = oportunidad
                anterior = Cotizacion.objects.select_for_update().filter(oportunidad=oportunidad, vigente=True).first()
                cotizacion.vigente = anterior is None
                cotizacion.save()
                if anterior:
                    reemplazar_cotizacion(cotizacion_actual_id=anterior.pk, cotizacion_nueva_id=cotizacion.pk)
                if conversacion:
                    conversacion.cotizacion = cotizacion  # Compatibilidad hasta retirar la FK legado.
                    conversacion.oportunidad_actual = oportunidad
                    conversacion.cliente = cotizacion.cliente
                    conversacion.save(update_fields=["cotizacion", "cliente", "oportunidad_actual", "actualizado"])
    destino = _DESTINOS_CREATE.get(request.POST.get("next"), "cotizaciones:list")
    return redirect(destino)


@login_required
def update_estado(request, pk):
    """
    Endpoint compartido: lo usa tanto el boton de estado de
    CotizacionesList.svelte como el arrastrar-y-soltar de
    TableroVendedor.svelte. La validacion de transiciones vive solo aca
    (Cotizacion.puede_transicionar_a) -- ningun frontend la reimplementa.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    nuevo_estado = request.POST.get("estado", "")
    if not cotizacion.puede_transicionar_a(nuevo_estado):
        return HttpResponseBadRequest("Transición de estado inválida.")

    transicionar_cotizacion(cotizacion_id=cotizacion.pk, nuevo_estado=nuevo_estado)
    return redirect("cotizaciones:list")


@login_required
def tablero(request):
    """
    FEAT-03 (evolucion): tablero Kanban de trabajo diario del vendedor --
    solo sus propias cotizaciones, nunca las de todo el equipo (eso es el
    Dashboard de Embudo del gerente, FEAT-05/SCRUM-15, aparte y pendiente).

    Tambien es donde vive la interfaz de WhatsApp consolidada (columna
    "Mensajes nuevos" + ChatFlotante) -- por eso pasa la lista de clientes:
    TableroVendedor.svelte la usa para el mini-formulario que crea una
    Cotizacion (via CotizacionForm, mismo endpoint create()) a partir de
    una conversacion que todavia no tiene una asociada.
    """
    oportunidades = Oportunidad.objects.filter(creado_por=request.user).select_related("lead", "etapa_actual").prefetch_related("cotizaciones")
    etapas = Etapa.objects.filter(pipeline__activo=True).select_related("pipeline")
    clientes = Cliente.objects.all()
    return render(request, "cotizaciones/tablero.html", {
        "oportunidades": oportunidades,
        "etapas": etapas,
        "conversaciones_nuevas": Conversacion.objects.filter(estado=Conversacion.Estado.NUEVA).count(),
        "clientes": clientes,
    })


@login_required
def mover_oportunidad(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    oportunidad = get_object_or_404(Oportunidad, pk=pk, creado_por=request.user)
    etapa = get_object_or_404(Etapa, pk=request.POST.get("etapa_id"))
    try:
        if etapa.tipo == Etapa.Tipo.GANADA:
            cerrar_oportunidad_ganada(oportunidad_id=oportunidad.pk, etapa_ganada=etapa, usuario=request.user)
        elif etapa.tipo == Etapa.Tipo.PERDIDA:
            cerrar_oportunidad_perdida(
                oportunidad_id=oportunidad.pk, etapa_perdida=etapa, usuario=request.user,
                motivo_perdida=request.POST.get("motivo_perdida", ""),
            )
        else:
            mover_oportunidad_de_etapa(oportunidad_id=oportunidad.pk, etapa_nueva=etapa, usuario=request.user)
    except Exception as error:
        return HttpResponseBadRequest(str(error))
    return JsonResponse({"ok": True, "etapa_id": etapa.id})


@login_required
def bandeja(request):
    """Bandeja compartida por sede. No hay asignacion por vendedor."""
    conversaciones = Conversacion.objects.select_related("sede", "cliente", "cotizacion").prefetch_related("mensajes")
    return render(request, "cotizaciones/bandeja.html", {
        "conversaciones": conversaciones,
        # No usamos `list(...)`: este modulo ya tiene una vista llamada
        # `list`, que ocultaria el built-in de Python. json_script recibe
        # solamente diccionarios JSON nativos.
        "sedes_data": [
            {"id": sede.id, "nombre": sede.nombre}
            for sede in Sede.objects.filter(activa=True)
        ],
        "clientes": Cliente.objects.all(),
    })


@login_required
def abrir_conversacion(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    conversacion = get_object_or_404(Conversacion, pk=pk)
    MensajeWhatsApp.objects.filter(
        conversacion=conversacion, direccion=MensajeWhatsApp.Direccion.ENTRANTE, leido=False
    ).update(leido=True)
    if conversacion.estado == Conversacion.Estado.NUEVA:
        conversacion.estado = Conversacion.Estado.ABIERTA
        conversacion.save(update_fields=["estado", "actualizado"])
    return JsonResponse({"ok": True, "estado": conversacion.estado})


@login_required
def enviar_mensaje_whatsapp(request, pk):
    """Persistencia local; el envio al proveedor se conectara en una fase posterior."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    conversacion = get_object_or_404(Conversacion, pk=pk)
    contenido = request.POST.get("contenido", "").strip()
    if not contenido:
        return HttpResponseBadRequest("El mensaje no puede estar vacio.")
    mensaje = MensajeWhatsApp.objects.create(
        conversacion=conversacion, direccion=MensajeWhatsApp.Direccion.SALIENTE, contenido=contenido, leido=True
    )
    if conversacion.estado in (Conversacion.Estado.NUEVA, Conversacion.Estado.PENDIENTE):
        conversacion.estado = Conversacion.Estado.ABIERTA
        conversacion.save(update_fields=["estado", "actualizado"])
    return JsonResponse({"id": mensaje.id, "contenido": mensaje.contenido, "creado": mensaje.creado.isoformat()})
