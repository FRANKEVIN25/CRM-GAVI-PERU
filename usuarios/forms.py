from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


class CrearAgenteForm(UserCreationForm):
    """
    Formulario para que GERENTE / ADMIN_CRM registren nuevos agentes
    desde el CRM, sin necesitar acceso al admin de Django.
    """

    first_name = forms.CharField(label="Nombre", max_length=150, required=True)
    last_name = forms.CharField(label="Apellido", max_length=150, required=True)
    email = forms.EmailField(label="Correo electrónico", required=True)

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "rol", "password1", "password2"]
        labels = {
            "username": "Usuario (para iniciar sesión)",
            "rol": "Rol en el CRM",
        }

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.first_name = self.cleaned_data["first_name"]
        usuario.last_name = self.cleaned_data["last_name"]
        usuario.email = self.cleaned_data["email"]
        # GERENTE y ADMIN_CRM necesitan is_staff para acceder al admin de Django.
        if usuario.rol in (Usuario.Rol.GERENTE, Usuario.Rol.ADMIN_CRM):
            usuario.is_staff = True
        if commit:
            usuario.save()
        return usuario
