from django.contrib import admin

from .models import Conversacion, MensajeWhatsApp, Sede


class MensajeWhatsAppInline(admin.TabularInline):
    model = MensajeWhatsApp
    extra = 0
    readonly_fields = ["creado"]


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ["nombre", "telefono_whatsapp", "activa"]


@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ["nombre_contacto", "telefono", "sede", "estado", "cliente", "cotizacion", "actualizado"]
    list_filter = ["sede", "estado"]
    search_fields = ["nombre_contacto", "telefono", "cliente__nombre"]
    inlines = [MensajeWhatsAppInline]
