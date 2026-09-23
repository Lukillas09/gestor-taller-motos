# Arquitectura

El proyecto usa un monolito Django modular:

```text
Django monolitico modular -> Railway -> Supabase PostgreSQL
```

Django concentra templates, autenticacion, reglas de negocio, vistas y admin en una sola aplicacion web. Las apps dentro de `apps/` separan responsabilidades sin convertir el sistema en microservicios.

La app `servicios` administra las visitas al taller y conserva una referencia histórica al cliente que era propietario al momento del registro. La app `mantenimientos` aporta en esta fase el catálogo de trabajos y la relación de trabajos realizados; los intervalos y alertas pertenecen a la Fase 3.

El alta y la edición de un servicio se ejecutan dentro de una transacción. La misma operación guarda el servicio, sincroniza sus mantenimientos y actualiza el último kilometraje conocido de la moto solo si el nuevo valor es mayor. El modelo bloquea la moto durante esa actualización para proteger el kilometraje ante registros concurrentes.

Railway sera el hosting de la aplicacion Django. Supabase se usara principalmente como PostgreSQL administrado en produccion.

La arquitectura evita Redis, Celery, servicios adicionales y frontend separado mientras no exista una necesidad concreta. Esto reduce costos, complejidad operativa y mantenimiento.

Las vistas privadas usan Django Auth. Los listados y filtros conservan un fallback HTTP normal y HTMX se limita a reemplazar resultados o mostrar el contexto de la moto seleccionada.

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
