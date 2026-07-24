# Modelo de dominio: Actividad y Tarea

**Documento:** decisión de diseño  
**Fecha:** 2026-07-23  
**Estado:** implementado  
**Jira:** SCRUM-25 (pendiente crear ticket)

---

## Problema que resuelve este documento

El modelo `Actividad` en `oportunidades/models.py` mezcla dos conceptos
ontológicamente distintos: un **registro histórico** (algo que ocurrió)
y una **tarea pendiente** (algo que debe ocurrir). Además, el modelo
`Seguimiento` existente cubre parcialmente el segundo concepto pero le
faltan campos clave y su asociación polimórfica está incompleta.

Este documento fija la separación definitiva y el diseño de cada objeto.

---

## Referencia: cómo distingue HubSpot los dos conceptos

HubSpot es la referencia de UX porque los vendedores del equipo GAVI
ya conocen ese vocabulario. Sus dos objetos relevantes:

| Objeto HubSpot | Qué es | Mutabilidad | ¿Tiene due date? |
|---|---|---|---|
| **Activity** | Registro de lo que ya ocurrió: llamada, nota, correo, WhatsApp | Inmutable una vez logueado | No (tiene timestamp de ocurrencia) |
| **Task** | Acción futura pendiente: "llamar mañana", "enviar cotización" | Mutable (open → completed / overdue) | Sí, requerido |

HubSpot también muestra que una `Task` tiene:
- **Título** (qué hacer, no solo "recordatorio")
- **Tipo**: Llamada, Correo, Reunión, LinkedIn... (no solo "tarea")
- **Prioridad**: Baja / Media / Alta
- **Notas** de contexto
- Asociación polimórfica: puede estar ligada a un Contacto, Negocio o Empresa

Nuestro `Seguimiento` actual solo tiene `fecha_recordatorio` y la FK
a `Cliente` (requerida) — no tiene título, ni tipo, ni prioridad, ni
notas. No puede existir sin un `Cliente`, lo que lo rompe en el nuevo
flujo donde el punto de entrada es un `Lead` (puede no tener `Cliente`
todavía).

---

## Objeto 1: `Actividad` — el log del timeline

### Propósito

Registro **inmutable** de algo que ya sucedió. Es la fuente de verdad
del historial de interacciones: qué pasó, cuándo y quién lo hizo.
Se muestra en el timeline de un `Lead` o una `Oportunidad`.

### Tipos válidos

| Tipo | Cuándo se crea |
|---|---|
| `nota` | El agente escribe un apunte libre sobre la conversación |
| `llamada` | Se loguea una llamada realizada |
| `whatsapp` | Mensaje WA entrante o saliente (se puede crear automáticamente desde `whatsapp/`) |

> `tarea` **no es un tipo válido de Actividad.** Las tareas son un
> objeto separado (ver más abajo). Cuando una `Tarea` se marca como
> completada, puede generar automáticamente una `Actividad` del tipo
> correspondiente — ese es el puente entre los dos objetos.

### Campos del modelo

```
content_type  FK → ContentType   (polimórfico: Lead u Oportunidad)
object_id     PositiveIntegerField
objeto        GenericForeignKey
tipo          CharField choices: nota / llamada / whatsapp
agente        FK → usuarios.Agente (SET_NULL)
descripcion   TextField
creado        DateTimeField (auto_now_add, inmutable)
```

**Implementado en:** `oportunidades/models.py`  
**Migración:** `oportunidades/migrations/0003_remove_actividad_completada_and_more.py`

### Invariantes

- Una vez creada, no se edita ni elimina (auditoría / Ley 29733).
- Siempre tiene `agente` o queda `null` si el agente fue eliminado.
- El `objeto` es siempre un `Lead` o una `Oportunidad`. No se engancha
  directamente a `Cliente` (el `Lead` ya tiene la FK al `Cliente`).

---

## Objeto 2: `Tarea` — la acción futura

### Propósito

Recordatorio accionable que el equipo usa para no perder un seguimiento.
Es mutable: se puede editar antes de vencer, marcar como completada,
reasignar. Reemplaza al `Seguimiento` actual con un modelo más rico.

### Por qué no copiamos HubSpot literalmente

HubSpot permite asociar una tarea a cualquier objeto del CRM (contacto,
empresa, negocio, etc.). Para GAVI eso es over-engineering: los vendedores
solo necesitan tareas sobre `Lead` y `Oportunidad`. Lo que sí adoptamos
de HubSpot es el vocabulario y los campos que hacen útil una tarea
(título, tipo, prioridad, notas).

### Lo que hacemos diferente (y mejor para el contexto GAVI)

**Completar una tarea genera automáticamente una `Actividad`.**
Si Isabel tiene una tarea "Llamar a taller Norte para confirmar cotización"
(tipo: llamada) y la marca como completada, el sistema crea un registro
`Actividad(tipo=llamada, descripcion=tarea.notas, objeto=tarea.objeto)`
en el timeline de la Oportunidad. El vendedor no tiene que loguearlo dos
veces. HubSpot tiene este comportamiento de forma manual; aquí lo hacemos
implícito.

### Campos del modelo

```
content_type       FK → ContentType   (polimórfico: Lead u Oportunidad)
object_id          PositiveIntegerField
objeto             GenericForeignKey
titulo             CharField(150)     — "Llamar para confirmar pedido"
tipo               CharField choices: llamada / correo / reunion / otro
prioridad          CharField choices: baja / media / alta  (default: media)
notas              TextField(blank)   — contexto extra, qué decir, qué pedir
fecha_vencimiento  DateTimeField      — requerido
asignada_a         FK → usuarios.Agente (SET_NULL) — puede reasignarse
creada_por         FK → usuarios.Agente (SET_NULL)
estado             CharField choices: PENDIENTE / COMPLETADA / VENCIDA
creado             DateTimeField(auto_now_add)
actualizado        DateTimeField(auto_now)
```

**Implementado en:** `tareas/models.py`, `tareas/services.py`  
**Migración:** `tareas/migrations/0001_initial.py`

### Mapeo tipo → Actividad al completar

| Tipo de Tarea | Actividad generada |
|---|---|
| `llamada` | `Actividad(tipo=LLAMADA)` |
| `correo` | `Actividad(tipo=NOTA)` |
| `reunion` | `Actividad(tipo=NOTA)` |
| `otro` | Sin actividad automática |

### Estado: derivado vs almacenado

`VENCIDA` es un estado **derivado** (fecha_vencimiento < ahora y no
completada), pero se almacena en BD para poder filtrar eficientemente
sin recalcular en cada request. Se actualiza vía `TareaQuerySet.marcar_vencidas()`
llamado al inicio de las vistas de listado, idéntico al patrón actual
de `SeguimientoQuerySet.actualizar_vencidos()`.

### Invariantes

- Una tarea `COMPLETADA` no se puede reabrir ni editar.
- Al completar una tarea de tipo `llamada`, `correo` o `reunion`, se
  crea automáticamente una `Actividad` del tipo correspondiente sobre
  el mismo `objeto`. Esto lo hace `tareas/services.py`, nunca el `save()`.
- El `objeto` es siempre un `Lead` o una `Oportunidad`.

---

## Relación entre los dos objetos

```
                                     ┌─────────────────┐
                                     │    Oportunidad  │
                                 ┌──▶│  (o Lead)       │◀──┐
                                 │   └─────────────────┘   │
                                 │                          │
              ┌──────────────┐   │ objeto (GFK)             │ objeto (GFK)
              │    Tarea     │───┘                          │
              │  (pendiente) │   al completar               │
              └──────┬───────┘   ──────────────▶  ┌────────┴─────────┐
                     │                             │    Actividad     │
                     │ crea automáticamente        │  (log histórico) │
                     └────────────────────────────▶└──────────────────┘
```

Una `Tarea` y la `Actividad` que genera apuntan al mismo `objeto`.
El timeline del Lead u Oportunidad muestra ambos en orden cronológico:
primero la `Actividad` (pasado), después las `Tarea`s pendientes (futuro).

---

## Migración desde `Seguimiento`

`Seguimiento` se reemplaza por `Tarea`. Plan incremental:

1. ✅ Modelo `Tarea` creado en `tareas/` con `0001_initial.py`.
2. **Pendiente:** migración de datos — cada `Seguimiento` existente se convierte
   en una `Tarea` con `tipo=otro`, `titulo="Seguimiento"`, el `objeto` apuntando
   al `Lead` o `Oportunidad` si existe, o al `Cliente` directamente si no.
3. **Pendiente:** una vez verificado en producción, deprecar el modelo `Seguimiento`.

`Seguimiento` sigue funcionando en producción hasta completar los pasos 2 y 3.

---

## Lo que NO cambia

- `Seguimiento` sigue funcionando en producción hasta que se migre.
- Los tests actuales de `seguimientos/` no se tocan hasta tener tests
  equivalentes en el modelo nuevo.
- `Actividad` en `oportunidades/models.py` solo se limpia (quitar TAREA,
  fecha_programada, completada) — no se mueve de app.
