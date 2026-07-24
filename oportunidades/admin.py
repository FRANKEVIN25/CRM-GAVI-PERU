from django.contrib import admin

from .models import Actividad, CambioEtapa, Etapa, Lead, Oportunidad, Pipeline


class EtapaInline(admin.TabularInline):
    model = Etapa
    extra = 0


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ["nombre", "activo"]
    inlines = [EtapaInline]


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre_contacto", "telefono", "origen", "agente_asignado", "creado"]
    list_filter = ["origen", "marca_interes"]
    search_fields = ["nombre_contacto", "telefono"]


@admin.register(Oportunidad)
class OportunidadAdmin(admin.ModelAdmin):
    list_display = ["id", "lead", "pipeline", "etapa_actual", "fecha_cierre_real"]
    list_filter = ["pipeline", "etapa_actual"]
    readonly_fields = ["pipeline", "etapa_actual", "fecha_cierre_real", "creado", "actualizado"]


@admin.register(CambioEtapa)
class CambioEtapaAdmin(admin.ModelAdmin):
    list_display = ["oportunidad", "etapa_anterior", "etapa_nueva", "agente", "timestamp"]
    readonly_fields = ["oportunidad", "etapa_anterior", "etapa_nueva", "agente", "timestamp"]


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ["tipo", "agente", "creado"]
    list_filter = ["tipo"]
