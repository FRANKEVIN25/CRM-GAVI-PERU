# CLAUDE.md — CRM GAVI PERU

Contexto para Claude Code en este repo. Leelo entero antes de tocar
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

FEAT-05 (dashboard de embudo de ventas) todavia no tiene app/vistas —
es semana 3. Cuando se implemente, que sea de solo lectura sobre estos
mismos modelos, no una app aparte con su propia logica duplicada.

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
(proyecto GAVI, clave por confirmar) y el Product Backlog en Drive.

## Comandos utiles

```bash
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
python3 manage.py test
```
