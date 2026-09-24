# Roadmap

## Fase 0 — Implementada

Base tecnica: Django, settings por entorno, apps iniciales, templates, PWA, deploy preparado y tests minimos.

## Fase 1 — Implementada

Gestión autenticada de clientes y motos: modelos, relación protegida, alta, listado, detalle, edición, archivado/restauración y búsqueda responsive con HTMX.

## Fase 2 — Implementada

Servicios e historial del taller: alta y edición transaccional, estados, cancelación sin borrado, kilometraje histórico, trabajos estructurados, filtros y búsqueda, ficha completa e historial por moto.

## Fase 3 — Implementada

Reglas configurables por meses y kilómetros, cálculo centralizado de estados, alertas operativas con filtros y HTMX, conteos y prioridades en dashboard, estado completo en la ficha de moto e interfaz para administrar el catálogo sin borrado físico.

## Fase 4 — Implementada

Seguimiento humano separado de las alertas técnicas: estados por ciclo y propietario, historial de eventos, contacto explícito, posposición, turno acordado, no interesado y reapertura. Incluye cola operativa derivada sin cron, integración manual con WhatsApp mediante `wa.me`, filtros y HTMX, dashboard y ficha de moto, administración, constraints, transacciones atómicas y tests de ciclo y propietario.

## Fase 4.1 — Implementada

Saneamiento y preparación para producción: auditoría de dominio, autenticación, URLs, consultas, dependencias, PWA y documentación; configuración moderna de estáticos con WhiteNoise; validación estricta de secretos; páginas de error seguras y pruebas de regresión. No requirió cambios de modelos ni migraciones.

## Fase 5

Exportaciones CSV, Excel y backups manuales.

## Fase 6

Mejoras avanzadas de experiencia de usuario y PWA.
