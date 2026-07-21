"""Normalización compartida de teléfonos para las entidades del CRM."""

import phonenumbers


def normalizar_e164(valor, region_por_defecto="PE"):
    """Devuelve un teléfono E.164 válido o ``None`` cuando no es interpretable.

    El valor original se conserva en Cliente.telefono para la visualización.
    Esta función no intenta adivinar países a partir de los últimos dígitos.
    """
    if not valor or not valor.strip():
        return None
    try:
        numero = phonenumbers.parse(valor, region_por_defecto)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(numero):
        return None
    return phonenumbers.format_number(numero, phonenumbers.PhoneNumberFormat.E164)
