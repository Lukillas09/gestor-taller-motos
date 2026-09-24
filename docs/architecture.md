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

## Seguimiento de alertas

La app `notificaciones` consume las alertas derivadas por `mantenimientos` y les superpone el seguimiento humano. La dependencia es unidireccional: `notificaciones` usa el servicio técnico de `mantenimientos`; el cálculo técnico no conoce los estados de contacto.

Una alerta técnica (`PROXIMO` o `VENCIDO`) y su seguimiento son conceptos distintos. Contactar, posponer o acordar un turno no cambia el estado técnico. El dashboard conserva los conteos técnicos y construye su cola de atención con el estado humano efectivo.

La superposición se realiza en lote: primero se calculan las alertas, luego se consultan todos los seguimientos relevantes y se combinan en memoria por `(mantenimiento_base_id, cliente_id)`. Los eventos sólo se cargan en la vista de historial. De este modo, las cards del dashboard, el listado y la ficha de moto no generan consultas por alerta.

Cada mutación recalcula y bloquea la moto y la regla dentro de `transaction.atomic`, comprueba que el mantenimiento base enviado como referencia siga siendo el ciclo actual, bloquea o crea el seguimiento y registra su evento en la misma transacción. Esto evita aplicar una acción abierta en una página vieja a un ciclo nuevo.

WhatsApp se integra exclusivamente mediante un enlace `wa.me` generado en el servidor con el propietario actual y un mensaje precargado. No hay API, envío automático ni llamada saliente desde el backend. Abrir el enlace tampoco registra contacto: el usuario debe ejecutar explícitamente la acción POST correspondiente.

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
