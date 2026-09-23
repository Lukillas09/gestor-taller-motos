# gestor-taller-motos

Aplicación web para la gestión de un taller de motos. El proyecto usa un monolito Django modular, responsive y PWA, con PostgreSQL como base objetivo y Supabase como PostgreSQL administrado en producción.

Las Fases 1 y 2 permiten gestionar clientes, motos y el historial completo de servicios, con trabajos de mantenimiento estructurados, kilometraje histórico y cancelación sin borrado físico.

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
- http://127.0.0.1:8000/servicios/
- http://127.0.0.1:8000/admin/

Las vistas operativas requieren iniciar sesión en `/accounts/login/`. El superusuario se crea de forma interactiva; el proyecto no incluye credenciales predeterminadas.

## Funcionalidad actual

- dashboard con cantidades reales de clientes y motos activas;
- clientes: alta, listado, detalle, edición, búsqueda y archivado/restauración;
- motos: alta, listado, detalle, edición, búsqueda y archivado/restauración;
- relación de un cliente con muchas motos protegida mediante `PROTECT`;
- búsqueda por nombre, apellido, teléfono, email, patente, marca y modelo;
- servicios con fecha histórica, estado, kilometraje, trabajos, observaciones y precio;
- conservación del cliente que era propietario al registrar cada servicio;
- catálogo administrable de tipos de mantenimiento y selección múltiple por servicio;
- actualización segura del último kilometraje, sin reducciones automáticas;
- cancelación de servicios conservando el historial;
- búsqueda y filtros de servicios por texto, estado y rango de fechas;
- historial real y responsive dentro de la ficha de cada moto;
- últimos cinco servicios y acceso rápido desde el dashboard;
- actualización de listados con HTMX y fallback mediante formularios GET;
- administración de clientes, motos, servicios y tipos de mantenimiento mediante Django Admin.

La patente se almacena en mayúsculas y sin espacios ni guiones. El kilometraje de una moto representa el último valor conocido por el taller, no una lectura en tiempo real.

Los intervalos de mantenimiento, vencimientos y alertas pertenecen a la Fase 3 y todavía no se calculan.

## Tests

La configuración de tests usa una base SQLite aislada en memoria y nunca utiliza `DATABASE_URL`:

```powershell
.\.venv\Scripts\python.exe manage.py test --settings=config.settings.test
```

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
