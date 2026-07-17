from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ["username", "email", "first_name", "last_name", "rol", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (("Rol", {"fields": ("rol",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Rol", {"fields": ("rol",)}),)
