from django import forms

from .models import Cotizacion


class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ["cliente", "descripcion_repuesto", "codigo_producto", "descuento_pct"]
