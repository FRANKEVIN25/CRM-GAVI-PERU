# Modelo de dominio — App `clientes`
*Revisión: 2026-07-23*

---

## 1. Problema que resuelve esta documentación

El modelo actual funciona, pero mezcla tres conceptos distintos en un solo
campo (`segmento`) y no tiene una forma explícita de saber en qué punto del
ciclo comercial se encuentra un cliente. Cuando el sistema escale —más
vendedores, más volumen, posible integración futura con gaviperu.com— esa
ambigüedad se convierte en deuda técnica cara.

Esta documentación propone:
1. Qué campos fundamentales agregar para alcanzar la flexibilidad de HubSpot.
2. Cómo hacerlo de forma incremental sin romper lo que ya funciona.
3. Qué **no** hacer todavía (para no sobreingieniar).

---

## 2. La lección de HubSpot y Odoo

### 2.1 La distinción Persona ↔ Empresa

HubSpot mantiene dos objetos separados pero enlazados:

```
Contact  (persona física)   ←──── Company (empresa/RUC)
  └── nombre, teléfono, cargo       └── razón social, RUC, sector
```

Odoo hace lo mismo con `res.partner` y el campo `company_type = person | company`,
donde una persona puede pertenecer a una empresa y la empresa puede tener
varios contactos.

**Por qué importa para GAVI:** hoy un `Cliente` puede ser Rodrigo (quien llama
personalmente) o Talleres Flores SAC (la empresa que paga). Son entidades con
ciclos de vida diferentes: Rodrigo puede cambiar de empresa, y la empresa puede
tener tres personas que llaman. Si no los distinguimos, el historial queda
mezclado y el handoff entre vendedores vuelve a romperse.

### 2.2 Etapa del ciclo de vida (Lifecycle Stage)

HubSpot tiene un campo `etapa_del_ciclo_de_vida` en el objeto Contacto,
**independiente del pipeline de ventas**. Representa el estado de la relación
total con ese contacto en el tiempo:

```
Lead → Lead calificado (MQL) → Lead calificado ventas (SQL)
     → Oportunidad → Cliente → Evangelista
```

Esto responde la pregunta: *¿Quién es esta persona para nosotros hoy?*
El pipeline (Etapa/Oportunidad en `oportunidades/models.py`) responde:
*¿En qué paso del proceso está esta venta específica?*

Son dos ejes distintos. Confundirlos es el error más común.

### 2.3 Estado del lead (Lead Status)

Solo existe cuando la etapa del ciclo de vida es `Lead` o `SQL`. Es un estado
operacional de corto plazo:

```
Nuevo → Intento de contacto → En curso → Negocio abierto → Sin calificar
```

Responde: *¿Qué está pasando operacionalmente con este lead ahora mismo?*
Desaparece (o pierde relevancia) cuando el contacto se convierte en Cliente.

---

## 3. Diagnóstico del modelo actual

### 3.1 Lo que está bien

| Elemento | Por qué es correcto |
|---|---|
| `Interaccion` separada de `Cliente` | Historial compartido entre vendedores, cumple el principio de memoria compartida |
| `Vehiculo` como entidad propia | Un cliente tiene N vehículos; no hay pérdida de datos al actualizarlo |
| `telefono_normalizado` E.164 | Permite deduplicar y buscar sin importar el formato ingresado |
| `Lead` en `oportunidades` con FK opcional a `Cliente` | Punto de entrada del funnel desacoplado del cliente registrado |

### 3.2 Los tres problemas de flexibilidad

**Problema A — `segmento` mezcla tipo de entidad con segmento comercial:**

```python
# Estado actual: un solo campo hace dos cosas
class Segmento(models.TextChoices):
    CONSUMO     = "CONSUMO"      # → tipo de transacción
    CORPORATIVO = "CORPORATIVO"  # → tipo de entidad (empresa)
    SEGUROS     = "SEGUROS"      # → canal/industria
    TALLER      = "TALLER"       # → tipo de entidad (empresa)
```

CORPORATIVO y TALLER describen *quién es* el cliente.
CONSUMO y SEGUROS describen *cómo compra*. No son la misma dimensión.

**Problema B — Sin etapa del ciclo de vida en `Cliente`:**

No hay forma de saber si un `Cliente` registrado es un comprador frecuente,
alguien que compró una sola vez hace un año, o un prospecto que nunca cerró.
El pipeline (`Oportunidad`) captura esto indirectamente, pero requiere una
query compleja para derivarlo.

**Problema C — La conversión Lead → Cliente no tiene trazabilidad formal:**

Cuando un `Lead` se convierte en `Cliente`, el vínculo existe como FK opcional
(`Lead.cliente`), pero no hay un campo en `Cliente` que diga
"este cliente llegó por el canal X, fue lead desde tal fecha".

---

## 4. Modelo objetivo — lo que el app `clientes` debe llegar a ser

### 4.1 Separación de dimensiones

```
Cliente
  ├── tipo_entidad:  NATURAL | EMPRESA          ← quién es
  ├── segmento:      MOSTRADOR | TALLER | SEGUROS | CORPORATIVO  ← cómo compra
  ├── etapa_ciclo:   PROSPECTO → LEAD → CLIENTE → RECURRENTE     ← dónde está en la relación
  └── estado_lead:   NUEVO | EN_CONTACTO | CALIFICADO | NO_CALIFICADO  ← solo si etapa = LEAD
```

Relación entre empresa y personas:

```
Cliente (tipo=EMPRESA)
  └── contactos: [Cliente (tipo=NATURAL), ...]  (FK empresa ← persona)
```

Esto permite: "Talleres Flores SAC tiene 3 personas que llaman, la última
interacción fue con Rodrigo el martes".

### 4.2 Diagrama de relaciones objetivo

```
┌─────────────────────────────────────────────────────────┐
│  Cliente                                                │
│  ─────────────────────────────────────────────────────  │
│  id, nombre, tipo_entidad (NATURAL|EMPRESA)             │
│  segmento (MOSTRADOR|TALLER|SEGUROS|CORPORATIVO)        │
│  etapa_ciclo (PROSPECTO|LEAD|CLIENTE|RECURRENTE)        │
│  estado_lead (NUEVO|EN_CONTACTO|CALIFICADO|NO_CALIFIC.) │
│  empresa_principal → Cliente(EMPRESA)  [nullable]       │
│  telefono, telefono_normalizado                         │
│  ruc [nullable, solo EMPRESA]                           │
│  fecha_registro, creado_por                             │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ↓                 ↓
   Vehiculo          Interaccion
   (sin cambios)     (sin cambios)
```

### 4.3 La etapa del ciclo de vida explicada para GAVI

```
PROSPECTO    → El número existe (en un Lead) pero aún no se ha registrado
               como Cliente. No aparece en la ficha de clientes todavía.

LEAD         → Fue registrado como Cliente pero nunca ha cerrado una venta.
               estado_lead activo: NUEVO | EN_CONTACTO | CALIFICADO | NO_CALIFIC.

CLIENTE      → Cerró al menos una Oportunidad (etapa tipo=GANADA).
               estado_lead ya no aplica.

RECURRENTE   → Tiene N cierres ganados (umbral configurable, ej. ≥ 3).
               Marca a los compradores de confianza para priorizar atención.
```

La transición `LEAD → CLIENTE` la dispara `oportunidades/services.py`
(`cerrar_oportunidad_ganada()`), no un campo editable a mano.

---

## 5. Plan de implementación incremental

### Fase 1 — Separar las dimensiones (sin romper nada)

Cambios en `clientes/models.py`:

1. Agregar `tipo_entidad = CharField(choices=TipoEntidad)` con default `NATURAL`.
2. Agregar `etapa_ciclo = CharField(choices=EtapaCiclo)` con default `LEAD`.
3. Agregar `estado_lead = CharField(choices=EstadoLead, null=True, blank=True)`.
4. Agregar `empresa_principal = ForeignKey('self', null=True, blank=True, limit_choices_to={'tipo_entidad': 'EMPRESA'})`.
5. Agregar `ruc = CharField(max_length=11, blank=True)`.
6. **No tocar** `segmento` todavía — existe en producción con datos reales.

Migración: todos los campos nuevos son `null=True` o tienen `default`, por lo
que es segura sin `RunPython`.

### Fase 2 — Automatizar la transición de etapa

En `oportunidades/services.py`, al ejecutar `cerrar_oportunidad_ganada()`,
actualizar `cliente.etapa_ciclo = 'CLIENTE'`.

Agregar signal o método de manager que calcule `RECURRENTE` en batch
(no en cada save — es una operación de reporting, no transaccional).

### Fase 3 — Migrar `segmento` a la nueva semántica

Auditar con management command los valores existentes, mapear
`CORPORATIVO → tipo_entidad=EMPRESA + segmento=CORPORATIVO`,
`TALLER → tipo_entidad=EMPRESA + segmento=TALLER`, etc.
Luego hacer el campo `segmento` consistente solo con tipos de transacción.

### Fase 4 — UI (fuera del scope de modelos)

Formulario de creación diferenciado por `tipo_entidad`: si es EMPRESA,
mostrar campo RUC; si es NATURAL, mostrar campo de empresa principal.
Esto es trabajo de `ClienteForm` y el template `create.html`.

---

## 6. Lo que NO hacer ahora

| Tentación | Por qué no |
|---|---|
| Crear apps separadas `personas/` y `empresas/` | El dominio es pequeño. Una tabla con `tipo_entidad` es suficiente y más simple de mantener |
| Hacer `etapa_ciclo` configurable por el Gerente (como los Pipelines) | Las etapas del ciclo de vida son universales al negocio, no por proceso. Solo Pipeline/Etapa en `oportunidades` necesita ser configurable |
| Integrar `ruc` con SUNAT para validar en tiempo real | Fuera del MVP. Un `CharField` con validación de longitud (11 dígitos) es suficiente por ahora |
| Agregar `email` a `Cliente` | No hay evidencia de necesidad en las entrevistas. El canal principal es WhatsApp. Agregar cuando haya un caso real |

---

## 7. Relación entre modelos de `clientes` y el resto del sistema

```
whatsapp.Conversacion ──────→ clientes.Cliente
                                    ↑
oportunidades.Lead ─────────────────┘  (FK opcional; Lead puede existir sin Cliente)
oportunidades.Oportunidad ──→ oportunidades.Lead
cotizaciones.Cotizacion ────→ clientes.Cliente
                         └──→ oportunidades.Oportunidad
seguimientos.Seguimiento ───→ clientes.Cliente
```

Un `Cliente` es el nodo central del sistema. Todo lo demás orbita alrededor.
La flexibilidad de escalar está en que ese nodo tenga las dimensiones correctas
(`tipo_entidad`, `etapa_ciclo`) sin duplicar lógica en cada app satélite.
