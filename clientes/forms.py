from django import forms

from .models import Cliente, Interaccion
from .telefonos import normalizar_e164


class ClienteForm(forms.ModelForm):
    placa = forms.CharField(max_length=20, required=False, label="Placa (opcional)")
    modelo = forms.CharField(max_length=100, required=False, label="Modelo (opcional)")

    class Meta:
        model = Cliente
        fields = ["nombre", "telefono", "segmento"]

    def clean_nombre(self):
        return " ".join(self.cleaned_data["nombre"].split())

    def clean_telefono(self):
        telefono = self.cleaned_data["telefono"].strip()
        if not normalizar_e164(telefono):
            raise forms.ValidationError("Ingresa un teléfono válido, por ejemplo +51 999 111 222.")
        return telefono

    def clean_placa(self):
        return self.cleaned_data["placa"].strip().upper()

    def clean_modelo(self):
        return " ".join(self.cleaned_data["modelo"].split())


class InteraccionForm(forms.ModelForm):
    class Meta:
        model = Interaccion
        fields = ["canal", "nota"]
