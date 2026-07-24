from django.contrib import admin

from .models import Tarea


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "tipo", "prioridad", "estado", "fecha_vencimiento", "asignada_a"]
    list_filter = ["estado", "tipo", "prioridad"]
    search_fields = ["titulo", "notas"]
    readonly_fields = ["creado", "actualizado"]
