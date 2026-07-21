from django.contrib import admin

from .models import Cotizacion


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ["id", "cliente", "usuario", "estado", "descuento_pct", "fecha"]
    list_filter = ["estado"]
    search_fields = ["cliente__nombre", "descripcion_repuesto"]
    readonly_fields = ["estado"]
