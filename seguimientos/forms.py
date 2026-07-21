from django import forms
from django.utils import timezone

from cotizaciones.models import Cotizacion

from .models import Seguimiento


class SeguimientoForm(forms.ModelForm):
    """Formulario de recordatorios; el responsable se toma de la sesion."""

    class Meta:
        model = Seguimiento
        fields = ["cliente", "cotizacion", "fecha_recordatorio"]
        widgets = {
            "fecha_recordatorio": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        cliente_inicial = kwargs.pop("cliente_inicial", None)
        super().__init__(*args, **kwargs)
        self.fields["cliente"].empty_label = "Selecciona un cliente"
        self.fields["cotizacion"].required = False
        self.fields["cotizacion"].queryset = Cotizacion.objects.select_related("cliente").all()
        if cliente_inicial:
            self.fields["cliente"].initial = cliente_inicial

    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get("cliente")
        cotizacion = cleaned_data.get("cotizacion")
        fecha = cleaned_data.get("fecha_recordatorio")

        if cotizacion and cliente and cotizacion.cliente_id != cliente.id:
            self.add_error("cotizacion", "La cotización debe pertenecer al cliente seleccionado.")
        if fecha and fecha < timezone.now():
            self.add_error("fecha_recordatorio", "El recordatorio debe programarse para una fecha futura.")
        return cleaned_data
