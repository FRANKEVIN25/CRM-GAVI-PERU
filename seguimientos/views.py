from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from clientes.models import Cliente

from .forms import SeguimientoForm
from .models import Seguimiento


@login_required
def listado(request):
    Seguimiento.objects.actualizar_vencidos()
    ahora = timezone.localtime()
    inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_hoy = inicio_hoy + timedelta(days=1)
    filtro = request.GET.get("estado", "pendientes")

    seguimientos = Seguimiento.objects.select_related("cliente", "cotizacion", "usuario")
    if filtro == "hoy":
        seguimientos = seguimientos.filter(
            fecha_recordatorio__gte=inicio_hoy,
            fecha_recordatorio__lt=fin_hoy,
        ).exclude(estado=Seguimiento.Estado.CUMPLIDO)
    elif filtro == "vencidos":
        seguimientos = seguimientos.filter(estado=Seguimiento.Estado.VENCIDO)
    elif filtro == "cumplidos":
        seguimientos = seguimientos.filter(estado=Seguimiento.Estado.CUMPLIDO)
    else:
        seguimientos = seguimientos.filter(
            Q(estado=Seguimiento.Estado.PENDIENTE) | Q(estado=Seguimiento.Estado.VENCIDO)
        )

    pendientes = Seguimiento.objects.filter(estado=Seguimiento.Estado.PENDIENTE)
    return render(request, "seguimientos/listado.html", {
        "seguimientos": seguimientos,
        "filtro": filtro,
        "total_hoy": pendientes.filter(fecha_recordatorio__gte=inicio_hoy, fecha_recordatorio__lt=fin_hoy).count(),
        "total_vencidos": Seguimiento.objects.filter(estado=Seguimiento.Estado.VENCIDO).count(),
    })


@login_required
def crear(request):
    cliente_inicial = None
    cliente_id = request.GET.get("cliente")
    if cliente_id:
        cliente_inicial = get_object_or_404(Cliente, pk=cliente_id)

    if request.method == "POST":
        form = SeguimientoForm(request.POST)
        if form.is_valid():
            seguimiento = form.save(commit=False)
            seguimiento.usuario = request.user
            seguimiento.save()
            return redirect("seguimientos:listado")
    else:
        form = SeguimientoForm(cliente_inicial=cliente_inicial)
    return render(request, "seguimientos/crear.html", {"form": form, "cliente_inicial": cliente_inicial})


@login_required
def marcar_cumplido(request, pk):
    if request.method != "POST":
        return redirect("seguimientos:listado")
    seguimiento = get_object_or_404(Seguimiento, pk=pk)
    if seguimiento.estado != Seguimiento.Estado.CUMPLIDO:
        seguimiento.estado = Seguimiento.Estado.CUMPLIDO
        seguimiento.save(update_fields=["estado"])
    return redirect(request.POST.get("next") or "seguimientos:listado")

# Create your views here.
