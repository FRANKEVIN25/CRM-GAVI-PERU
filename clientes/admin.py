from django.contrib import admin

from .models import Cliente, Interaccion, Vehiculo


class VehiculoInline(admin.TabularInline):
    model = Vehiculo
    extra = 1
    readonly_fields = ["creado_por"]


class InteraccionInline(admin.TabularInline):
    model = Interaccion
    extra = 0
    readonly_fields = ["fecha"]


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "telefono", "segmento", "creado_por", "fecha_registro"]
    list_filter = ["segmento"]
    search_fields = ["nombre", "telefono"]
    inlines = [VehiculoInline, InteraccionInline]

    def save_model(self, request, obj, form, change):
        if not change and not obj.creado_por_id:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Interaccion) and not instance.pk:
                instance.usuario = request.user
            if isinstance(instance, Vehiculo) and not instance.pk and not instance.creado_por_id:
                instance.creado_por = request.user
            instance.save()
        formset.save_m2m()
