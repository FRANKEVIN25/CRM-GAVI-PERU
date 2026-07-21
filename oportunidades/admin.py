from django.contrib import admin

from .models import CambioEtapa, Etapa, Oportunidad, Pipeline


class EtapaInline(admin.TabularInline):
    model = Etapa
    extra = 0


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ["nombre", "activo"]
    inlines = [EtapaInline]


@admin.register(Oportunidad)
class OportunidadAdmin(admin.ModelAdmin):
    list_display = ["id", "cliente", "pipeline", "etapa", "cerrada_en"]
    list_filter = ["pipeline", "etapa"]
    readonly_fields = ["pipeline", "etapa", "cerrada_en", "creado", "actualizado"]


@admin.register(CambioEtapa)
class CambioEtapaAdmin(admin.ModelAdmin):
    list_display = ["oportunidad", "etapa_anterior", "etapa_nueva", "cambiado_por", "cambiado_en"]
    readonly_fields = ["oportunidad", "etapa_anterior", "etapa_nueva", "cambiado_por", "cambiado_en"]
