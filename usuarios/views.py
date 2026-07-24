from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.views import View

from .forms import CrearAgenteForm
from .models import Usuario


class RedireccionPorRolView(LoginRequiredMixin, View):
    """
    Destino de LOGIN_REDIRECT_URL. Redirige según el rol:
    - GERENTE / ADMIN_CRM con is_staff → al admin de Django
    - Todos los demás → al CRM (lista de cotizaciones)
    Si el usuario no tiene rol definido cae al CRM también.
    """

    def get(self, request):
        rol = getattr(request.user, "rol", None)
        if rol in (Usuario.Rol.GERENTE, Usuario.Rol.ADMIN_CRM) and request.user.is_staff:
            return redirect("/admin/")
        return redirect("/cotizaciones/")


class _SoloAdminsGerentes(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin: permite acceso solo a GERENTE y ADMIN_CRM."""

    def test_func(self):
        rol = getattr(self.request.user, "rol", None)
        return rol in (Usuario.Rol.GERENTE, Usuario.Rol.ADMIN_CRM)


class ListaAgentesView(_SoloAdminsGerentes, View):
    template_name = "usuarios/agentes.html"

    def get(self, request):
        agentes = Usuario.objects.order_by("first_name", "username")
        return render(request, self.template_name, {"agentes": agentes})


class CrearAgenteView(_SoloAdminsGerentes, View):
    template_name = "usuarios/crear_agente.html"

    def get(self, request):
        return render(request, self.template_name, {"form": CrearAgenteForm()})

    def post(self, request):
        form = CrearAgenteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("usuarios:agentes")
        return render(request, self.template_name, {"form": form})
