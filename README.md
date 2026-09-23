# gestor-taller-motos

Aplicación web para la gestión de un taller de motos. El proyecto usa un monolito Django modular, responsive y PWA, con PostgreSQL como base objetivo y Supabase como PostgreSQL administrado en producción.

La Fase 1 permite gestionar clientes y motos, buscar por datos operativos, consultar detalles y archivar o restaurar registros sin borrarlos físicamente.

## Tecnologias

- Python
- Django
- Django Templates
- HTMX
- Bootstrap 5
- PostgreSQL mediante `DATABASE_URL`
- WhiteNoise
- Gunicorn
- openpyxl para futuras exportaciones Excel

## Requisitos

- Python 3.12 o compatible con Django 5
- PostgreSQL para desarrollo real o Supabase PostgreSQL en produccion

Para una primera ejecucion local, si `DATABASE_URL` queda vacio, Django usa SQLite solo como fallback de desarrollo.

## Instalación

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abrir:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/clientes/
- http://127.0.0.1:8000/motos/
- http://127.0.0.1:8000/admin/

Las vistas operativas requieren iniciar sesión en `/accounts/login/`. El superusuario se crea de forma interactiva; el proyecto no incluye credenciales predeterminadas.

## Funcionalidad actual

- dashboard con cantidades reales de clientes y motos activas;
- clientes: alta, listado, detalle, edición, búsqueda y archivado/restauración;
- motos: alta, listado, detalle, edición, búsqueda y archivado/restauración;
- relación de un cliente con muchas motos protegida mediante `PROTECT`;
- búsqueda por nombre, apellido, teléfono, email, patente, marca y modelo;
- actualización de listados con HTMX y fallback mediante formularios GET;
- administración básica mediante Django Admin.

La patente se almacena en mayúsculas y sin espacios ni guiones. El kilometraje de una moto representa el último valor conocido por el taller, no una lectura en tiempo real.

## Variables de entorno

Copiar `.env.example` como `.env` y completar los valores necesarios:

```env
DEBUG=True
SECRET_KEY=change-me
DATABASE_URL=
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=
DJANGO_SETTINGS_MODULE=config.settings.development
```

En produccion, `DATABASE_URL` debe apuntar a PostgreSQL, por ejemplo Supabase.

## Estructura

```text
config/                 Configuracion Django y settings por entorno
apps/                   Apps internas del proyecto
templates/              Templates globales
static/                 CSS, JS, manifest y service worker
docs/                   Documentación de producto y arquitectura
tests/                  Espacio para tests transversales futuros
```

## Railway

El proyecto incluye `Procfile` y `railway.json`. En Railway configurar variables de entorno de produccion, incluyendo:

- `DJANGO_SETTINGS_MODULE=config.settings.production`
- `SECRET_KEY`
- `DATABASE_URL`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`

El comando de inicio definido ejecuta migraciones, `collectstatic` y luego Gunicorn.
