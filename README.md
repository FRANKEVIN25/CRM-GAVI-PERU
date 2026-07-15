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

## Sprints

- **Semana 1** — ficha de cliente compartida + historial
- **Semana 2** — cotizaciones + recordatorios
- **Semana 3** — panel de numeros para el gerente (FEAT-05)

Backlog completo con criterios de aceptacion: ver Jira (proyecto por
confirmar) y el Product Backlog en Drive.
