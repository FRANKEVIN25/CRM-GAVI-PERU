# CRM GAVI PERU

Sistema de seguimiento de clientes para Autopartes GAVI PERU — memoria
compartida del equipo de ventas, no un sistema de vigilancia.

Desarrollado por Hanan Technology Group (Frank Jauregui + Franklin).

## Stack

Django + PostgreSQL + Redis, desplegado en AWS EC2 con Nginx. Ver el
detalle completo de cada decision de arquitectura en el DAS (Google Drive,
carpeta `CRM GAVI PERU / 04. Arquitectura`).

## Setup local

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Genera una SECRET_KEY real:
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Pegala en .env

python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

Sin `DATABASE_URL` en `.env`, el proyecto corre con sqlite local
automaticamente — util para desarrollar sin instalar Postgres.

## Estructura

Monolito modular — una app de Django por dominio, no microservicios
(la razon esta en el DAS, seccion 1):

- `usuarios` — autenticacion y roles (FEAT-00)
- `clientes` — ficha de cliente, vehiculos, historial de interacciones (FEAT-01, FEAT-02)
- `cotizaciones` — cotizaciones con estado y descuentos (FEAT-03, FEAT-06)
- `seguimientos` — recordatorios de seguimiento (FEAT-04)

## FEAT-00 y FEAT-01 — estado y validación

### FEAT-00: autenticación y roles básicos

- El modelo `usuarios.Usuario` extiende el usuario de Django: cada persona
  tiene `username` único y contraseña almacenada con hash.
- Incluye los roles `VENDEDOR` y `GERENTE`, administrables en `/admin/`.
- Todas las rutas de clientes requieren una sesión iniciada. La creación de
  clientes y vehículos guarda al usuario responsable; las interacciones ya
  guardan también su autor. Es trazabilidad para facilitar el handoff, no una
  métrica de productividad.

### FEAT-01: ficha de cliente única

- `/clientes/` permite buscar por nombre, teléfono o placa.
- La ficha muestra nombre, teléfono, segmento y todos los vehículos/placas.
- Al crear, se normaliza la placa y se advierte con enlaces a las fichas que
  coinciden por nombre, teléfono o placa; no se crea un duplicado.

### Pruebas

```bash
python3 manage.py migrate
python3 manage.py test
```

Las pruebas cubren el acceso autenticado, las tres vías de búsqueda, la
advertencia de duplicados y la atribución del registro a quien lo creó.

La guía de continuidad técnica, rutas, modelo de datos y comandos de
verificación está en [docs/feat-00-feat-01.md](docs/feat-00-feat-01.md).

## Frontend Svelte (islas dentro de Django)

Django sigue manejando todas las rutas, vistas y auth. Svelte solo
añade interactividad en la ficha de cliente: la línea de tiempo de
interacciones y el formulario para registrar una nueva.

### Setup

```bash
cd frontend
npm install
```

### Desarrollo (HMR)

Corre el servidor de Vite en paralelo con Django:

```bash
# Terminal 1
cd frontend && npm run dev      # Vite en localhost:5173

# Terminal 2
python manage.py runserver      # Django en localhost:8000
```

La primera vez que abras la ficha de un cliente, el navegador cargará
los módulos de Svelte desde el dev server. Los cambios en `.svelte`
se reflejan al recargar la página (el HMR completo requeriría que Django
sirva el HTML desde Vite, lo cual no aplica a este patrón de islas).

### Build para producción

```bash
cd frontend && npm run build
```

Genera `clientes/static/clientes/dist/` con los archivos con hash y
`manifest.json`. Django sirve esos archivos como estáticos normales.

**Hay que rebuildear antes de cada deploy si hubo cambios en `frontend/src/`.**
El templatetag `{% vite_tags %}` detecta automáticamente si hay un
manifest (producción) o no (dev server); no hace falta cambiar nada
en los templates al alternar entre entornos.

### Cómo funciona la conexión Django ↔ Svelte

1. La vista `detail` renderiza el template normalmente.
2. `{% interacciones_data_script %}` embebe las interacciones como JSON
   en un `<script type="application/json" id="interacciones-data">`.
3. `main.js` lo lee al cargar, monta `Timeline.svelte` con esos datos
   y monta `InteraccionForm.svelte` con la URL y el token CSRF del DOM.
4. Al guardar una interacción, el form hace `fetch()` POST al endpoint
   Django existente (`clientes/views.py:add_interaccion`), y despacha
   un evento DOM para que Timeline actualice sin recargar la página.

## Sprints

- **Semana 1** — ficha de cliente compartida + historial
- **Semana 2** — cotizaciones + recordatorios
- **Semana 3** — panel de numeros para el gerente (FEAT-05)

Backlog completo con criterios de aceptacion: ver Jira (proyecto por
confirmar) y el Product Backlog en Drive.
