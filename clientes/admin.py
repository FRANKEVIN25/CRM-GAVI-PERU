from django.contrib import admin

from .models import Cliente, Interaccion, Vehiculo


class VehiculoInline(admin.TabularInline):
    model = Vehiculo
    extra = 1


class InteraccionInline(admin.TabularInline):
    model = Interaccion
    extra = 0
    readonly_fields = ["fecha"]


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "telefono", "segmento", "fecha_registro"]
    list_filter = ["segmento"]
    search_fields = ["nombre", "telefono"]
    inlines = [VehiculoInline, InteraccionInline]
