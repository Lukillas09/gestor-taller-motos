# gestor-taller-motos

Base tecnica para una aplicacion web de gestion de taller de motos. El proyecto esta preparado como monolito Django simple, responsive y PWA, con PostgreSQL como base objetivo y Supabase como PostgreSQL administrado en produccion.

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

## Instalacion

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Abrir:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/admin/

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
docs/                   Documentacion inicial
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
