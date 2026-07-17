# Entrega técnica — FEAT-00 y FEAT-01

Fecha de implementación: 17 de julio de 2026
Commit base: `e979b26`

Este documento describe lo entregado en autenticación, roles y ficha única
de cliente. El propósito es que cualquier integrante del equipo pueda levantar
el proyecto y continuar desde la misma base.

## FEAT-00 — Autenticación y roles básicos

### Alcance entregado

- `usuarios.Usuario` extiende `AbstractUser`, por lo que cada integrante tiene
  un `username` único y una contraseña gestionada y hasheada por Django.
- El campo `rol` tiene dos valores: `VENDEDOR` y `GERENTE`.
- El administrador de Django muestra y permite asignar el rol al crear o editar
  usuarios (`/admin/`).
- Las pantallas de clientes requieren inicio de sesión. Si una persona no está
  autenticada, Django la redirige a `/accounts/login/`.
- La creación de un cliente o vehículo almacena el usuario responsable en
  `creado_por`. Las interacciones ya almacenan su autor en `usuario`.

La atribución existe para que un compañero pueda retomar un caso con contexto;
no debe usarse para rankings ni control de productividad.

### Rutas involucradas

| Ruta | Uso |
| --- | --- |
| `/accounts/login/` | Inicio de sesión mediante las vistas incorporadas de Django. |
| `/accounts/logout/` | Cierre de sesión. |
| `/admin/` | Alta de usuarios y asignación de rol por usuarios autorizados. |

## FEAT-01 — Ficha de cliente única

### Alcance entregado

- La búsqueda en `/clientes/` acepta coincidencias por nombre, teléfono o
  placa, sin distinguir mayúsculas/minúsculas en nombre y placa.
- La ficha individual muestra nombre, teléfono, segmento, vehículos/placas y
  la persona que registró al cliente.
- Un cliente puede tener varios vehículos mediante la relación `Vehiculo`.
- Al crear un cliente, la placa se normaliza a mayúsculas. Antes de guardar se
  busca una coincidencia exacta por nombre, teléfono o placa. Si existe, se
  muestra una advertencia y enlaces a las fichas encontradas; no se crea un
  registro duplicado.

### Rutas involucradas

| Ruta | Uso |
| --- | --- |
| `/clientes/` | Búsqueda y listado de clientes. |
| `/clientes/new/` | Registro de cliente y vehículo opcional. |
| `/clientes/<id>/` | Ficha única del cliente. |

## Modelo de datos relevante

```text
Usuario ──< Cliente (creado_por)
Usuario ──< Vehiculo (creado_por)
Cliente ──< Vehiculo
Usuario ──< Interaccion >── Cliente
```

Los campos `creado_por` son opcionales únicamente para conservar
compatibilidad con datos existentes al aplicar la migración. Todo registro
nuevo creado desde las pantallas o el admin queda atribuido automáticamente.

## Archivos principales

- `usuarios/models.py`: usuario personalizado y roles.
- `usuarios/admin.py`: administración de roles.
- `clientes/models.py`: cliente, vehículo e interacción.
- `clientes/forms.py`: normalización de los datos del formulario.
- `clientes/views.py`: acceso autenticado, búsqueda, duplicados y creación.
- `clientes/admin.py`: atribución automática cuando se usa el admin.
- `clientes/tests.py`: pruebas funcionales de los criterios de aceptación.

## Preparación y verificación

```bash
python3 manage.py migrate
python3 manage.py test
python3 manage.py check
```

Las cuatro pruebas actuales validan: acceso protegido, búsqueda por los tres
criterios, advertencia de duplicado por placa y trazabilidad del usuario que
crea cliente/vehículo.

## Continuidad

Antes de crear una nueva migración, ejecutar:

```bash
python3 manage.py makemigrations --check --dry-run
```

No se deben modificar las migraciones ya compartidas. Los cambios de modelo
nuevos deben generar una migración adicional y revisarse antes de producción.
