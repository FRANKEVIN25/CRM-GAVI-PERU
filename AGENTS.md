# AGENTS.md — CRM GAVI PERU

Contexto para Codex en este repo. Leelo entero antes de tocar
codigo — evita que tengamos que re-explicar todo esto cada sesion.

## Que es esto

CRM a medida para Autopartes GAVI PERU (Lima, distribuidor de repuestos
automotrices, marcas chinas). Cliente real, no proyecto de curso.
Desarrollado por Hanan Technology Group — Frank Jauregui + Franklin,
ambos como developers.

## El problema que resuelve (no perder esto de vista)

GAVI pierde ~91% de sus contactos comerciales sin convertirlos en venta.
La causa no es falta de demanda: la relacion con el cliente vive repartida
en metodos informales sin punto en comun entre el equipo (Excel personal,
agendas fisicas, WhatsApp archivado). Cuando alguien deja a un cliente a
medias, nadie mas puede retomarlo porque no hay historial compartido.

## Principio de diseno no negociable

**El sistema es memoria compartida, no vigilancia.** Karina (Jefa de
Ventas) e Isabel, en las entrevistas de descubrimiento, mostraron
resistencia directa a sentirse controladas o perder su autonomia de
negociacion. Cualquier feature que se sienta como control de desempeno
en vez de ayuda pone en riesgo que el equipo lo adopte. El log de
auditoria existe por cumplimiento de la Ley 29733 (trazabilidad de datos
personales), NUNCA como reporte de productividad por vendedor.

## Stack y arquitectura

Django + PostgreSQL + Redis, EC2 + Nginx + Gunicorn + SSL (Let's Encrypt).

**Monolito modular, no microservicios** — decision deliberada: un solo
dominio de negocio, sin necesidad de escalar partes por separado ni
coordinar equipos distintos. Apps de Django separadas por dominio para
poder extraer servicios en el futuro SI algun dia hay evidencia real de
necesitarlo, sin tener que rediseñar desde cero.

**Sin integraciones externas en el MVP** — ni con gaviperu.com (la tienda
online, tambien construida por Hanan) ni con el sistema de productos de
GAVI. Ambas decisiones fueron confirmadas explicitamente por el gerente
(riesgo de mostrar stock desactualizado). El campo `codigo_producto` en
Cotizacion es un puente de texto libre para una integracion futura, no
una FK a un catalogo real — no lo conviertas en una sin que alguien lo
pida con evidencia de negocio detras.

DAS completo con todas las decisiones y su justificacion: Google Drive,
carpeta `CRM GAVI PERU / 04. Arquitectura (DAS)`.

## Apps del proyecto

- `usuarios` — modelo `Usuario` (extiende AbstractUser), campo `rol`
  (VENDEDOR / GERENTE). FEAT-00.
- `clientes` — `Cliente`, `Vehiculo`, `Interaccion`. Un cliente tiene
  varios vehiculos y varias interacciones registradas por cualquier
  usuario, no solo quien lo atendio primero. FEAT-01, FEAT-02.
- `cotizaciones` — `Cotizacion` con estado (enviada/confirmada/
  convertida/perdida) y `descuento_pct`. FEAT-03, FEAT-06.
- `seguimientos` — `Seguimiento`, recordatorio ligado a un Cliente y
  opcionalmente a una Cotizacion especifica. FEAT-04.
- `whatsapp` — `Sede`, `Conversacion`, `MensajeWhatsApp`. Bandeja
  compartida por sede (no por vendedor, no hay "reclamo" individual de
  chats). Sin vistas propias a proposito: la interfaz vive consolidada
  dentro de `/cotizaciones/` (ver `cotizaciones/views.py` y los tests
  `test_no_existe_ruta_de_whatsapp` en `cotizaciones/tests.py` y
  `whatsapp/tests.py`) — es una decision de UX ya tomada y probada, no
  un pendiente.

FEAT-05 (dashboard de embudo de ventas) todavia no tiene app/vistas —
es semana 3. Cuando se implemente, que sea de solo lectura sobre estos
mismos modelos, no una app aparte con su propia logica duplicada.

**En evolucion (ver seccion siguiente):** esta aprobada una app nueva
`oportunidades` (Pipeline/Etapa/Oportunidad) y una evolucion de
`whatsapp` para soportar un BSP real. Ningun modelo ni migracion de esto
existe todavia salvo lo que la seccion de abajo marca explicitamente
como hecho.

## Decisión de arquitectura: Oportunidad/Pipeline/Etapa (2026-07-21)

Contexto completo, modelo objetivo campo por campo, diagrama de
relaciones, flujo mensaje-a-cierre, estrategia de migracion incremental
y plan de commits: documento "Auditoria del modelo de dominio y
propuesta de evolucion — CRM GAVI PERU" (Claude Code, revision 3;
pedirselo a Frank si no lo tienes a mano — vive fuera del repo, no en
`docs/`, ver la nota sobre esa carpeta en el historial de git).

Resumen para no tener que abrir el documento completo cada vez:

- `Cotizacion` deja de ser el unico mecanismo de pipeline. Se agrega
  `oportunidades` con `Pipeline` (configurable), `Etapa` (ordenadas, tipo
  EN_PROGRESO/GANADA/PERDIDA) y `Oportunidad` (el proceso comercial;
  `Cotizacion` sigue siendo el documento/oferta dentro de ese proceso —
  una Oportunidad puede acumular varias Cotizacion en el tiempo, solo una
  `vigente` a la vez).
- Cerrar una Oportunidad (ganada/perdida) es EXCLUSIVAMENTE a traves de
  `cerrar_oportunidad_ganada()`/`cerrar_oportunidad_perdida()` en
  `oportunidades/services.py` — nunca en `save()`, nunca por edicion
  directa en el admin, nunca dejando una inconsistencia "para revisar
  despues". Si las precondiciones no se cumplen (p. ej. la cotizacion
  vigente todavia no esta confirmada), el cierre completo se bloquea con
  un error claro, sin escribir nada.
- `whatsapp` evoluciona para poder recibir un BSP real algun dia: numero
  de WhatsApp como entidad propia (`NumeroWhatsApp`, ya no un `CharField`
  en `Sede`), idempotencia real de webhooks y de mensajes, adjuntos (solo
  metadata por ahora, sin descarga ni almacenamiento propio). Sigue sin
  conectarse ningun proveedor real (Twilio/Meta) — son solo los puntos de
  extension.
- Telefonos se normalizan a E.164 en el backend (libreria `phonenumbers`,
  todavia no agregada como dependencia), nunca con la regla de "ultimos 9
  digitos" que hoy solo vive en el frontend (`normalizarTelefono` en
  `chats.svelte.js`).
- Migracion estrictamente incremental: nada se resta sin auditar antes
  los datos existentes (`clientes/management/commands/auditar_datos_dominio.py`,
  ya escrito y corrido contra la base local — pendiente correrlo tambien
  contra produccion antes de agregar restricciones nuevas) y sin dejar
  las columnas viejas como legado hasta verificar en produccion.

Jira: proyecto `CRM_GAVI_PERU`, clave **`SCRUM`** (esto resuelve la
"clave por confirmar" de la seccion de sprints, mas abajo). Ticket de
esta decision de arquitectura: **SCRUM-24**.

## Convenciones

- Nombres de campos y modelos en español (`nombre`, `telefono`,
  `descuento_pct`), consistente con toda la documentacion del proyecto.
- Comentarios de codigo en español cuando expliquen una decision de
  negocio; en ingles esta bien para detalles puramente tecnicos.
- Variables de entorno via `django-environ`, nunca secretos hardcodeados
  — `.env` esta en `.gitignore`, usa `.env.example` como plantilla.
- Migraciones: revisar siempre a mano antes de aplicar en produccion,
  sobre todo cambios de esquema en `Cliente` o `Cotizacion` con datos
  reales ya cargados (ver DAS, riesgos de produccion).

## Plan de sprints (3 semanas)

1. **Semana 1** — `usuarios` + `clientes` completos (ficha + historial).
   Esto ya resuelve el dolor #1 (handoff entre companeros) aunque no
   haya cotizaciones todavia.
2. **Semana 2** — `cotizaciones` + `seguimientos`.
3. **Semana 3** — Dashboard (FEAT-05) con datos reales ya acumulados.

Backlog completo con criterios de aceptacion y story points: Jira
(proyecto `CRM_GAVI_PERU`, clave `SCRUM`) y el Product Backlog en Drive.

## Comandos utiles

```bash
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
python3 manage.py test
```
