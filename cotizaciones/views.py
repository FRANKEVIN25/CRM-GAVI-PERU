from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from clientes.models import Cliente

from .forms import CotizacionForm
from .models import Cotizacion


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
}


@login_required
def create(request):
    if request.method == "POST":
        form = CotizacionForm(request.POST)
        if form.is_valid():
            cotizacion = form.save(commit=False)
            cotizacion.usuario = request.user
            cotizacion.save()
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
