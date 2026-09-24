# Arquitectura

El proyecto usa un monolito Django modular:

```text
Django monolitico modular -> Railway -> Supabase PostgreSQL
```

Django concentra templates, autenticacion, reglas de negocio, vistas y admin en una sola aplicacion web. Las apps dentro de `apps/` separan responsabilidades sin convertir el sistema en microservicios.

La app `servicios` administra las visitas al taller y conserva una referencia histórica al cliente que era propietario al momento del registro. La app `mantenimientos` administra el catálogo, las reglas configurables, los trabajos realizados y el cálculo de próximos mantenimientos.

El alta y la edición de un servicio se ejecutan dentro de una transacción. La misma operación guarda el servicio, sincroniza sus mantenimientos y actualiza el último kilometraje conocido de la moto solo si el nuevo valor es mayor. El modelo bloquea la moto durante esa actualización para proteger el kilometraje ante registros concurrentes.

Railway sera el hosting de la aplicacion Django. Supabase se usara principalmente como PostgreSQL administrado en produccion.

La arquitectura evita Redis, Celery, servicios adicionales y frontend separado mientras no exista una necesidad concreta. Esto reduce costos, complejidad operativa y mantenimiento.

Las vistas privadas usan Django Auth. Los listados y filtros conservan un fallback HTTP normal y HTMX se limita a reemplazar resultados o mostrar el contexto de la moto seleccionada.

## Cálculo de mantenimientos

La fuente de verdad está en `apps/mantenimientos/services.py`. Ese servicio de dominio suma meses calendario, selecciona el último mantenimiento válido por moto y tipo, calcula los límites de fecha y kilometraje y devuelve estados derivados. Dashboard, alertas y ficha de moto consumen el mismo resultado y no repiten reglas en vistas o templates.

Solo reinicia un ciclo un `MantenimientoRealizado` asociado a un servicio `FINALIZADO` cuya fecha no sea futura. Los servicios `ABIERTO` y `CANCELADO` se conservan en el historial, pero no intervienen en este cálculo. El último registro se decide por `Servicio.fecha`, con desempate estable por identificadores.

Las alertas no se persisten. Se calculan al abrir las pantallas usando tres consultas principales: tipos activos configurados, motos activas con su cliente actual activo y mantenimientos válidos con sus relaciones precargadas. El agrupamiento por `(moto_id, tipo_id)` se realiza en memoria para evitar N+1. No se requieren caché, cron, workers, Redis ni Celery.

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
