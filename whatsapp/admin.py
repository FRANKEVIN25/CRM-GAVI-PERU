from django.contrib import admin

from .models import Conversacion, EventoWebhookWhatsApp, MensajeWhatsApp, NumeroWhatsApp, Sede


class MensajeWhatsAppInline(admin.TabularInline):
    model = MensajeWhatsApp
    extra = 0
    readonly_fields = ["creado"]


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ["nombre", "telefono_whatsapp", "activa"]


@admin.register(NumeroWhatsApp)
class NumeroWhatsAppAdmin(admin.ModelAdmin):
    list_display = ["telefono", "sede", "proveedor", "activo"]
    list_filter = ["proveedor", "activo", "sede"]
    search_fields = ["telefono", "proveedor_numero_id", "proveedor_cuenta_id"]


@admin.register(EventoWebhookWhatsApp)
class EventoWebhookWhatsAppAdmin(admin.ModelAdmin):
    list_display = ["evento_id_proveedor", "proveedor", "recibido_en", "procesado"]
    list_filter = ["proveedor", "procesado"]
    search_fields = ["evento_id_proveedor", "payload_hash", "error"]
    readonly_fields = [
        "numero", "proveedor", "evento_id_proveedor", "payload_hash", "payload",
        "recibido_en", "procesado", "error",
    ]


@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ["nombre_contacto", "telefono", "sede", "estado", "cliente", "cotizacion", "actualizado"]
    list_filter = ["sede", "estado"]
    search_fields = ["nombre_contacto", "telefono", "cliente__nombre"]
    inlines = [MensajeWhatsAppInline]
