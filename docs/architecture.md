# Arquitectura

El proyecto usa un monolito Django modular:

```text
Django monolitico modular -> Railway -> Supabase PostgreSQL
```

Django concentra templates, autenticacion, reglas de negocio, vistas y admin en una sola aplicacion web. Las apps dentro de `apps/` separan responsabilidades sin convertir el sistema en microservicios.

Railway sera el hosting de la aplicacion Django. Supabase se usara principalmente como PostgreSQL administrado en produccion.

La arquitectura evita Redis, Celery, servicios adicionales y frontend separado mientras no exista una necesidad concreta. Esto reduce costos, complejidad operativa y mantenimiento.

## Multi-taller futuro

La aplicacion nace para un unico taller. Aun asi, se documenta la posibilidad futura de soportar:

```text
Taller
├ Usuarios
├ Clientes
├ Motos
└ Servicios
```

No se implementa multi-tenant en esta fase para evitar complejidad prematura.
