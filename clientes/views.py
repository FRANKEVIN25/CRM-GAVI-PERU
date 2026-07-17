from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Cliente, Vehiculo
from .forms import ClienteForm


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
    cliente = get_object_or_404(Cliente.objects.prefetch_related("vehiculos"), pk=pk)
    return render(request, "clientes/detail.html", {"cliente": cliente})


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
