from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Cliente, Interaccion, Vehiculo
from .forms import ClienteForm, InteraccionForm


@login_required
def lista_contactos(request):
    """Lista paginable de personas naturales — equivalente a Contactos en HubSpot."""
    q = request.GET.get("q", "").strip()
    etapa = request.GET.get("etapa", "")
    estado = request.GET.get("estado", "")

    qs = (
        Cliente.objects
        .filter(tipo_entidad=Cliente.TipoEntidad.NATURAL)
        .select_related("empresa_principal", "creado_por")
        .order_by("-fecha_registro")
    )
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(telefono__icontains=q))
    if etapa:
        qs = qs.filter(etapa_ciclo=etapa)
    if estado:
        qs = qs.filter(estado_lead=estado)

    return render(request, "clientes/contactos.html", {
        "contactos": qs,
        "q": q,
        "etapa_activa": etapa,
        "estado_activo": estado,
        "etapas": Cliente.EtapaCiclo.choices,
        "estados": Cliente.EstadoLead.choices,
        "total": qs.count(),
    })


@login_required
def lista_empresas(request):
    """Lista paginable de clientes tipo EMPRESA — equivalente a Empresas en HubSpot."""
    q = request.GET.get("q", "").strip()
    segmento = request.GET.get("segmento", "")

    qs = (
        Cliente.objects
        .filter(tipo_entidad=Cliente.TipoEntidad.EMPRESA)
        .annotate(num_contactos=Count("contactos"))
        .select_related("creado_por")
        .order_by("-fecha_registro")
    )
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(ruc__icontains=q) | Q(telefono__icontains=q))
    if segmento:
        qs = qs.filter(segmento=segmento)

    return render(request, "clientes/empresas.html", {
        "empresas": qs,
        "q": q,
        "segmento_activo": segmento,
        "segmentos": Cliente.Segmento.choices,
        "total": qs.count(),
    })


@login_required
def search(request):
    q = request.GET.get("q", "").strip()
    clientes = Cliente.objects.all().prefetch_related("vehiculos")
    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q)
            | Q(telefono__icontains=q)
            | Q(vehiculos__placa__icontains=q)
        ).distinct()
    return render(request, "clientes/search.html", {"clientes": clientes, "q": q})


@login_required
def detail(request, pk):
    cliente = get_object_or_404(
        Cliente.objects.prefetch_related("vehiculos", "interacciones__usuario"),
        pk=pk,
    )
    return render(request, "clientes/detail.html", {
        "cliente": cliente,
        "interaccion_form": InteraccionForm(),
    })


@login_required
def add_interaccion(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        form = InteraccionForm(request.POST)
        if form.is_valid():
            interaccion = form.save(commit=False)
            interaccion.cliente = cliente
            interaccion.usuario = request.user
            interaccion.save()
    return redirect("clientes:detail", pk=pk)


@login_required
def create(request):
    duplicates = None
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data["nombre"]
            telefono = form.cleaned_data["telefono"]
            placa = form.cleaned_data["placa"]

            duplicate_filter = Q(nombre__iexact=nombre) | Q(telefono=telefono)
            if placa:
                duplicate_filter |= Q(vehiculos__placa__iexact=placa)
            duplicates = Cliente.objects.filter(duplicate_filter).distinct()

            if duplicates.exists():
                pass
            else:
                cliente = Cliente.objects.create(
                    nombre=nombre,
                    telefono=telefono,
                    segmento=form.cleaned_data["segmento"],
                    creado_por=request.user,
                )
                if placa:
                    Vehiculo.objects.create(
                        cliente=cliente,
                        placa=placa,
                        modelo=form.cleaned_data["modelo"],
                        creado_por=request.user,
                    )
                return redirect("clientes:detail", pk=cliente.pk)
    else:
        form = ClienteForm()
    return render(request, "clientes/create.html", {"form": form, "duplicates": duplicates})
