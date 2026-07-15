from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    FEAT-00: Autenticacion y Roles Basicos.
    Extiende el usuario estandar de Django (ya trae username, email,
    password hasheado, etc.) y le agrega el rol que define el DAS.
    """

    class Rol(models.TextChoices):
        VENDEDOR = "VENDEDOR", "Vendedor"
        GERENTE = "GERENTE", "Gerente"

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.VENDEDOR)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"
