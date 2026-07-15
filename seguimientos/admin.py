from django.contrib import admin

from .models import Seguimiento


@admin.register(Seguimiento)
class SeguimientoAdmin(admin.ModelAdmin):
    list_display = ["cliente", "usuario", "fecha_recordatorio", "estado"]
    list_filter = ["estado"]
