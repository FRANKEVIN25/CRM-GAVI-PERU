"""
Auditoria de datos existentes, de solo lectura -- no escribe nada en la base.

Contexto: antes de agregar restricciones nuevas (UniqueConstraint en Vehiculo,
CheckConstraint de descuento_pct en Cotizacion) o de asumir que los datos ya
son validos (choices de Cliente.segmento), hace falta saber si los datos
reales de produccion ya violan esas reglas. Este comando responde eso.

Ver "Auditoria del modelo de dominio y propuesta de evolucion -- CRM GAVI
PERU", Seccion E (Etapa 0), para el contexto completo de por que existen
estos cuatro chequeos puntuales y no otros.

Uso:
    python manage.py auditar_datos_dominio
"""
import re
from collections import defaultdict

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.db.models.functions import Upper


def _normalizar_telefono_provisional(telefono):
    """
    Heuristica de solo-lectura para esta auditoria -- NO es la normalizacion
    E.164 definitiva que se implementara con la libreria `phonenumbers` en
    Cliente.telefono_normalizado (ver Seccion B de la propuesta). Se usa aqui,
    dependencia-libre, solo para detectar colisiones probables entre numeros
    ya guardados con formatos distintos, y darle a alguien un reporte para
    revisar a mano -- no para decidir nada de forma automatica.
    """
    solo_digitos = re.sub(r"\D", "", telefono or "")
    if len(solo_digitos) == 9 and not solo_digitos.startswith("51"):
        solo_digitos = "51" + solo_digitos
    return "+" + solo_digitos if solo_digitos else ""


class Command(BaseCommand):
    help = "Audita datos existentes antes de agregar restricciones nuevas de esquema. Solo lectura."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            "Auditoria de datos de dominio -- CRM GAVI PERU (solo lectura)"
        ))

        hubo_hallazgos = False
        hubo_hallazgos |= self._auditar_segmentos_invalidos()
        hubo_hallazgos |= self._auditar_placas_repetidas()
        hubo_hallazgos |= self._auditar_descuentos_fuera_de_rango()
        hubo_hallazgos |= self._auditar_telefonos_duplicados()

        self.stdout.write("")
        if hubo_hallazgos:
            self.stdout.write(self.style.WARNING(
                "Resultado: hay filas que revisar antes de agregar las restricciones "
                "condicionadas de la Seccion E (UniqueConstraint de Vehiculo, "
                "CheckConstraint de descuento_pct)."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Resultado: no se encontraron filas que bloqueen las restricciones "
                "condicionadas de la Seccion E."
            ))

    def _auditar_segmentos_invalidos(self):
        Cliente = apps.get_model("clientes", "Cliente")
        valores_validos = set(Cliente.Segmento.values)
        invalidos = (
            Cliente.objects
            .exclude(segmento__in=valores_validos)
            .values("id", "nombre", "segmento")
            .order_by("id")
        )
        total = len(invalidos)

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_LABEL(
            f"1. Segmentos invalidos (fuera de {sorted(valores_validos)}): {total}"
        ))
        if total:
            self.stdout.write(
                "   Residuo esperado de clientes/migrations/0003_alter_cliente_segmento.py "
                "(cambio de choices sin data migration -- hallazgo #14 de la auditoria)."
            )
            for fila in invalidos[:20]:
                self.stdout.write(f"   - Cliente #{fila['id']} \"{fila['nombre']}\": segmento actual = {fila['segmento']!r}")
            if total > 20:
                self.stdout.write(f"   ... y {total - 20} mas.")
        return total > 0

    def _auditar_placas_repetidas(self):
        Vehiculo = apps.get_model("clientes", "Vehiculo")
        grupos = (
            Vehiculo.objects
            .annotate(placa_norm=Upper("placa"))
            .values("cliente_id", "placa_norm")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
            .order_by("cliente_id", "placa_norm")
        )
        total_grupos = len(grupos)

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_LABEL(
            f"2. Placas repetidas bajo el mismo cliente (case-insensitive): {total_grupos} grupo(s)"
        ))
        if total_grupos:
            self.stdout.write(
                "   Bloquean la UniqueConstraint(cliente, placa) propuesta -- revisar caso por "
                "caso antes de agregarla (commit 17 de la Seccion G)."
            )
            for grupo in grupos[:20]:
                self.stdout.write(
                    f"   - Cliente #{grupo['cliente_id']}, placa {grupo['placa_norm']!r}: "
                    f"{grupo['total']} filas"
                )
            if total_grupos > 20:
                self.stdout.write(f"   ... y {total_grupos - 20} mas.")
        return total_grupos > 0

    def _auditar_descuentos_fuera_de_rango(self):
        Cotizacion = apps.get_model("cotizaciones", "Cotizacion")
        fuera_de_rango = (
            Cotizacion.objects
            .filter(Q(descuento_pct__lt=0) | Q(descuento_pct__gt=100))
            .values("id", "cliente_id", "descuento_pct")
            .order_by("id")
        )
        total = len(fuera_de_rango)

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_LABEL(
            f"3. Cotizaciones con descuento_pct fuera de [0, 100]: {total}"
        ))
        if total:
            self.stdout.write(
                "   Bloquean el CheckConstraint propuesto -- corregir antes de agregarlo "
                "(commit 16 de la Seccion G)."
            )
            for fila in fuera_de_rango[:20]:
                self.stdout.write(
                    f"   - Cotizacion #{fila['id']} (cliente #{fila['cliente_id']}): "
                    f"descuento_pct = {fila['descuento_pct']}"
                )
            if total > 20:
                self.stdout.write(f"   ... y {total - 20} mas.")
        return total > 0

    def _auditar_telefonos_duplicados(self):
        Cliente = apps.get_model("clientes", "Cliente")
        agrupados = defaultdict(list)
        for cliente_id, nombre, telefono in Cliente.objects.values_list("id", "nombre", "telefono"):
            clave = _normalizar_telefono_provisional(telefono)
            if clave:
                agrupados[clave].append((cliente_id, nombre, telefono))

        colisiones = {clave: filas for clave, filas in agrupados.items() if len(filas) > 1}
        total_grupos = len(colisiones)

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_LABEL(
            f"4. Telefonos que colisionan tras normalizar (heuristica provisional): {total_grupos} grupo(s)"
        ))
        self.stdout.write(
            "   Informativo unicamente -- no bloquea ninguna restriccion nueva (Cliente.telefono_normalizado "
            "no lleva UniqueConstraint, por decision de negocio: una linea puede corresponder a mas de un "
            "cliente/taller). Sirve para distinguir errores de tipeo reales de casos legitimos de linea compartida."
        )
        if total_grupos:
            for clave, filas in list(colisiones.items())[:20]:
                detalle = ", ".join(f"#{cid} \"{nombre}\" ({tel})" for cid, nombre, tel in filas)
                self.stdout.write(f"   - {clave}: {detalle}")
            if total_grupos > 20:
                self.stdout.write(f"   ... y {total_grupos - 20} mas.")
        return False  # informativo: nunca cuenta como bloqueante
