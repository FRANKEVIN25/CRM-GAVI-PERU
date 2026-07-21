from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from clientes.models import Cliente

from .forms import CotizacionForm
from .models import Cotizacion
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
            cotizacion = form.save(commit=False)
            cotizacion.usuario = request.user
            cotizacion.save()
            # La oportunidad nace desde la conversacion elegida; el vinculo
            # permite ver el historial de WhatsApp durante todo el pipeline.
            conversacion_id = request.POST.get("conversacion_id")
            if conversacion_id:
                conversacion = Conversacion.objects.filter(pk=conversacion_id).first()
                if conversacion:
                    conversacion.cotizacion = cotizacion
                    conversacion.cliente = cotizacion.cliente
                    conversacion.save(update_fields=["cotizacion", "cliente", "actualizado"])
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

    cotizacion.estado = nuevo_estado
    cotizacion.save(update_fields=["estado", "actualizado"])
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
    cotizaciones = Cotizacion.objects.filter(usuario=request.user).select_related("cliente")
    clientes = Cliente.objects.all()
    return render(request, "cotizaciones/tablero.html", {
        "cotizaciones": cotizaciones,
        "estados": Cotizacion.Estado.choices,
        "clientes": clientes,
    })


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
