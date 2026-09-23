# AGENTS.md

Este archivo contiene las instrucciones principales para cualquier agente de IA que trabaje sobre este repositorio.

Debe leerse completamente antes de analizar, modificar o crear código.

Las instrucciones de este archivo tienen prioridad sobre decisiones implícitas tomadas a partir del código existente.

---

# 1. Proyecto

Este repositorio contiene una aplicación web para la gestión de un taller de motos.

El sistema debe permitir al taller administrar principalmente:

* clientes;
* motos;
* historial de servicios;
* mantenimientos realizados;
* kilometraje;
* próximos mantenimientos;
* mantenimientos vencidos;
* recordatorios;
* seguimiento de contacto con clientes;
* contacto mediante WhatsApp;
* observaciones mecánicas;
* exportaciones y backups.

El flujo principal del producto es:

Cliente
→ Moto
→ Servicio
→ Mantenimiento
→ Alerta
→ Contacto

Toda funcionalidad nueva debe evaluarse según cuánto mejora este flujo.

---

# 2. Objetivo del producto

El sistema está pensado inicialmente para un taller pequeño con aproximadamente 1 o 2 usuarios.

Debe ser:

* simple;
* rápido;
* fácil de aprender;
* cómodo desde computadora;
* cómodo desde celular;
* económico de mantener;
* seguro;
* fácil de desarrollar por una sola persona.

Una persona que abre la aplicación debe poder entender en pocos segundos:

* qué necesita atención;
* qué motos están próximas a mantenimiento;
* qué clientes debe contactar;
* cómo registrar un nuevo servicio;
* cómo encontrar una moto o cliente.

La aplicación no debe sentirse como un sistema administrativo complicado.

---

# 3. Principio principal de UX

La información importante debe estar a la vista.

Evitar:

* menús profundos;
* navegación innecesaria;
* formularios enormes;
* acciones escondidas;
* pantallas sobrecargadas;
* demasiados clics para tareas frecuentes.

Priorizar:

* acciones rápidas;
* búsqueda;
* tarjetas claras;
* estados visuales;
* botones grandes en móvil;
* formularios simples;
* información contextual.

Las tareas habituales del mecánico deben requerir la menor cantidad de pasos posible.

---

# 4. Stack tecnológico obligatorio

## Backend

Python + Django.

## Frontend

Django Templates + HTMX.

## CSS

Bootstrap 5.

## Base de datos

PostgreSQL.

## Producción

Supabase PostgreSQL.

## Hosting

Railway.

## Repositorio

GitHub.

## Aplicación móvil

Progressive Web App (PWA).

## Autenticación

Django Auth.

## Contacto con clientes

Enlaces directos a WhatsApp mediante `wa.me`.

## Exportaciones

CSV y Excel.

Para Excel utilizar `openpyxl`.

## Archivos estáticos

WhiteNoise.

## Servidor producción

Gunicorn.

---

# 5. Tecnologías que NO deben introducirse sin una necesidad real

No agregar:

* React;
* Vue;
* Angular;
* Next.js;
* Flutter;
* React Native;
* Redis;
* Celery;
* RabbitMQ;
* Kafka;
* microservicios;
* frontend separado;
* Django REST Framework;
* GraphQL;
* Firebase;
* Supabase Auth;
* Supabase como API principal;
* WebSockets;
* infraestructura adicional.

Si una funcionalidad puede resolverse razonablemente con Django + PostgreSQL, esa debe ser la solución preferida.

No introducir una dependencia nueva si Python, Django, PostgreSQL o Bootstrap ya permiten resolver el problema de forma clara.

---

# 6. Filosofía de arquitectura

El proyecto utiliza un:

Django monolítico modular.

No es un microservicio ni debe evolucionar prematuramente hacia microservicios.

Las diferentes responsabilidades están separadas mediante aplicaciones Django.

Actualmente:

apps/core
apps/clientes
apps/motos
apps/servicios
apps/mantenimientos
apps/notificaciones
apps/exportaciones

Cada aplicación debe mantener una responsabilidad clara.

Evitar dependencias circulares entre apps.

---

# 7. Responsabilidad de las aplicaciones

## core

Elementos generales del sistema:

* dashboard;
* navegación;
* componentes globales;
* helpers compartidos;
* utilidades generales;
* configuración común.

No convertir `core` en un lugar donde colocar cualquier código que no tenga ubicación clara.

---

## clientes

Responsable de:

* datos de clientes;
* datos de contacto;
* dirección;
* teléfono;
* email;
* notas;
* estado del cliente.

---

## motos

Responsable de:

* motos;
* propietario;
* patente;
* marca;
* modelo;
* año;
* cilindrada;
* kilometraje;
* número de chasis;
* número de motor;
* observaciones específicas del vehículo.

---

## servicios

Responsable de:

* ingresos al taller;
* órdenes de servicio;
* historial;
* fecha;
* kilometraje;
* trabajos realizados;
* precios;
* observaciones del servicio;
* estado del trabajo.

---

## mantenimientos

Responsable de:

* tipos de mantenimiento;
* mantenimiento realizado;
* intervalos;
* fechas próximas;
* kilómetros próximos;
* reglas de mantenimiento.

Ejemplos:

* cambio de aceite;
* filtro de aceite;
* filtro de aire;
* bujías;
* cadena;
* pastillas de freno;
* líquido de freno;
* refrigerante;
* cubiertas;
* batería;
* service general.

---

## notificaciones

Responsable de:

* mantenimientos vencidos;
* mantenimientos próximos;
* seguimiento de contacto;
* recordatorios;
* estados del contacto.

No debe encargarse de enviar mensajes automáticamente mediante APIs pagas salvo que sea solicitado explícitamente en el futuro.

---

## exportaciones

Responsable de:

* CSV;
* Excel;
* exportaciones;
* backups descargables.

---

# 8. Mantenimientos configurables

Nunca asumir reglas rígidas como:

"el aceite dura exactamente un año".

Los intervalos deben ser configurables.

Un tipo de mantenimiento puede tener:

* intervalo temporal;
* intervalo por kilómetros;
* aviso anticipado.

Ejemplo:

Cambio de aceite:

* cada 12 meses;
* o cada 6000 km;
* avisar 30 días antes.

Cuando existan ambos límites, considerar que el mantenimiento puede necesitar atención al alcanzarse cualquiera de ellos.

No hardcodear estos valores en vistas ni templates.

---

# 9. Kilometraje

El kilometraje es un dato importante del sistema.

Cada service debería registrar el kilometraje de la moto en ese momento.

Esto permitirá posteriormente calcular:

último mantenimiento:

23.450 km

intervalo:

6.000 km

próximo:

29.450 km

La aplicación no debe asumir que conoce automáticamente el kilometraje actual de la moto.

Sólo trabajar con kilometrajes registrados.

---

# 10. Alertas

No utilizar inicialmente workers, Celery ni cron jobs para calcular alertas.

Las alertas pueden derivarse desde PostgreSQL cuando el usuario accede a la aplicación.

Ejemplo conceptual:

fecha_próxima <= hoy

→ vencido

fecha_próxima <= hoy + período_de_aviso

→ próximo

Lo mismo debe aplicarse a los kilómetros cuando exista información suficiente.

Los estados visuales principales serán:

* vencido;
* próximo;
* al día.

---

# 11. Seguimiento de contacto

Una alerta no debe desaparecer simplemente porque se contacte al cliente.

Debe existir un seguimiento separado.

Estados futuros posibles:

* pendiente;
* contactado;
* turno acordado;
* realizado;
* no interesado;
* pospuesto.

Debe registrarse cuando sea útil:

* fecha;
* usuario;
* observación;
* próximo recordatorio.

El sistema debe evitar que dos personas contacten repetidamente al mismo cliente por desconocer si ya fue avisado.

---

# 12. WhatsApp

No integrar inicialmente WhatsApp Business API.

Utilizar enlaces:

https://wa.me/

con un mensaje precargado.

El usuario debe tener control sobre el envío final.

Ejemplo conceptual:

Hola Carlos, ¿cómo estás?

Te contactamos desde Taller X.

Según nuestro registro, tu Honda Tornado se encuentra próxima al cambio de aceite.

Si querés podemos coordinar un turno.

No enviar mensajes automáticamente sin intervención del usuario.

---

# 13. Búsqueda

La búsqueda será una funcionalidad principal.

Debe priorizarse la posibilidad de encontrar rápidamente por:

* patente;
* nombre;
* apellido;
* teléfono;
* marca;
* modelo.

En un taller suele ser más práctico encontrar una moto mediante patente que navegar por distintas pantallas.

Las búsquedas frecuentes deben ser rápidas y accesibles.

---

# 14. Historial de moto

Cada moto debe tener una ficha clara.

La ficha deberá permitir ver progresivamente:

* propietario;
* datos básicos;
* kilometraje conocido;
* historial completo;
* servicios;
* mantenimientos;
* próximas tareas;
* observaciones mecánicas;
* contacto del propietario.

Debe ser posible comprender rápidamente qué se hizo anteriormente sobre una moto.

---

# 15. Observaciones mecánicas

Debe ser posible registrar notas como:

* revisar cubierta trasera;
* pérdida de aceite;
* cadena con desgaste;
* batería débil.

Las observaciones pendientes deberían poder aparecer cuando la moto vuelve al taller.

No mezclar estas observaciones con simples notas administrativas si requieren seguimiento.

---

# 16. Nuevo service

Registrar un service debe ser una de las operaciones más rápidas de la aplicación.

Ejemplo de futura experiencia:

Seleccionar moto.

Ingresar kilometraje.

Seleccionar:

* cambio aceite;
* filtro;
* frenos;
* cadena;
* etc.

Agregar observaciones.

Agregar precio.

Guardar.

Al guardar, los mantenimientos correspondientes deben quedar actualizados automáticamente mediante lógica de negocio centralizada.

---

# 17. Dashboard

El dashboard debe responder principalmente:

¿Qué necesita atención hoy?

Debe mostrar progresivamente:

* mantenimientos vencidos;
* mantenimientos próximos;
* últimos servicios;
* clientes pendientes de contacto;
* acciones rápidas.

Evitar llenar el dashboard con estadísticas decorativas sin utilidad operativa.

---

# 18. Responsive

Toda funcionalidad debe diseñarse desde el inicio pensando tanto en escritorio como móvil.

No desarrollar una vista exclusivamente desktop para luego intentar adaptarla.

En móvil:

* botones suficientemente grandes;
* evitar tablas horizontales enormes;
* usar cards cuando sean más cómodas;
* formularios simples;
* acciones principales visibles;
* navegación accesible.

---

# 19. PWA

La aplicación debe seguir siendo instalable como PWA.

No cachear de manera insegura:

* información privada;
* páginas autenticadas;
* información sensible de clientes.

No implementar offline complejo salvo requerimiento futuro.

La PWA busca principalmente:

* instalación en teléfono;
* sensación de aplicación;
* acceso rápido.

---

# 20. Seguridad

Aplicar las prácticas estándar de seguridad de Django.

Nunca:

* guardar contraseñas manualmente;
* guardar contraseñas en texto plano;
* deshabilitar CSRF sin motivo;
* hardcodear secretos;
* subir `.env`;
* guardar credenciales en Git;
* confiar en datos enviados por formularios;
* permitir acceso anónimo a datos privados una vez implementada autenticación real.

Utilizar:

* Django Auth;
* permisos;
* validaciones;
* CSRF;
* HTTPS en producción;
* cookies seguras en producción.

---

# 21. Datos personales

El sistema contiene información privada de clientes.

Mostrar sólo la información necesaria.

Evitar incluir información del cliente en:

* logs;
* excepciones;
* URLs innecesariamente;
* servicios externos.

No exponer información mediante endpoints públicos.

---

# 22. PostgreSQL

PostgreSQL es la base de datos oficial.

Supabase proporciona PostgreSQL en producción.

Evitar escribir código dependiente exclusivamente de SQLite.

SQLite puede existir únicamente como comodidad de desarrollo mientras esté claramente separado de producción.

Antes de implementar lógica sensible a concurrencia, restricciones o comportamiento SQL, considerar PostgreSQL como referencia real.

---

# 23. Supabase

Supabase se utilizará principalmente como:

PostgreSQL administrado.

No trasladar lógica de negocio a Supabase.

La lógica debe permanecer en Django.

No usar Supabase Auth.

No depender de la API automática de Supabase si Django ORM puede realizar la operación.

En el futuro puede utilizarse Supabase Storage para archivos si existe una necesidad concreta.

---

# 24. Railway

Railway ejecutará la aplicación Django.

El objetivo es mantener:

un único servicio web.

Evitar:

* workers innecesarios;
* Redis;
* servicios auxiliares;
* procesos permanentes sin necesidad.

La aplicación debe intentar mantener costos mínimos.

---

# 25. Archivos

No guardar permanentemente información del negocio en el filesystem de Railway.

El filesystem del servidor no debe considerarse almacenamiento persistente.

Si en el futuro se guardan:

* fotos;
* documentos;
* presupuestos;

usar almacenamiento externo apropiado.

---

# 26. Costos

Este proyecto tiene una restricción importante:

mantener costos operativos mínimos.

Antes de introducir un servicio pago o infraestructura adicional, analizar si realmente es necesaria.

Preferir soluciones incluidas en:

* Django;
* PostgreSQL;
* Railway;
* Supabase;
* GitHub.

---

# 27. Código

Priorizar código:

* claro;
* explícito;
* corto;
* mantenible;
* testeable.

Evitar:

* abstracciones prematuras;
* patrones innecesarios;
* clases genéricas difíciles de entender;
* código excesivamente ingenioso.

Una persona debe poder volver al código meses después y entenderlo con facilidad.

---

# 28. Nombres

Usar nombres claros y consistentes.

El dominio y la interfaz pueden utilizar español.

Mantener consistencia dentro del código.

No mezclar arbitrariamente nombres españoles e ingleses para el mismo concepto.

Ejemplos aceptables:

Cliente
Moto
Servicio
TipoMantenimiento
MantenimientoRealizado

---

# 29. Lógica de negocio

No colocar lógica importante directamente dentro de templates.

Evitar también concentrar toda la lógica dentro de vistas.

Cuando una operación de negocio crezca, moverla a:

* métodos de modelo;
* servicios;
* selectores;
* utilidades específicas;

según corresponda.

No crear capas vacías simplemente para seguir un patrón.

---

# 30. Consultas

Evitar problemas N+1.

Utilizar cuando sea apropiado:

* select_related;
* prefetch_related;
* índices;
* restricciones.

No optimizar prematuramente consultas que no presentan problemas reales.

---

# 31. Integridad de datos

Preferir garantizar invariantes importantes tanto mediante Django como mediante PostgreSQL.

Utilizar cuando corresponda:

* ForeignKey;
* UniqueConstraint;
* CheckConstraint;
* índices.

No depender exclusivamente de validaciones frontend.

---

# 32. Eliminación de datos

Antes de utilizar `CASCADE`, analizar el dominio.

No permitir que eliminar accidentalmente un cliente borre silenciosamente todo un historial mecánico importante sin considerar las consecuencias.

El historial de servicios es información valiosa para el taller.

Pensar cuidadosamente estrategias como:

* PROTECT;
* SET_NULL;
* archivado;
* baja lógica.

---

# 33. Fechas y horas

Utilizar timezone-aware datetimes mediante Django.

No implementar manualmente zonas horarias.

Mostrar fechas de manera adecuada para Argentina en la interfaz.

---

# 34. Dinero

Cuando se agreguen precios:

usar `DecimalField`.

Nunca utilizar float para dinero.

---

# 35. Migraciones

Toda modificación de modelos debe considerar migraciones.

Antes de finalizar cambios de modelos ejecutar:

python manage.py makemigrations --check

o generar la migración correspondiente si fue solicitada.

No editar migraciones históricas ya desplegadas salvo una razón extraordinaria.

No crear migraciones vacías innecesarias.

---

# 36. Tests

Toda lógica de negocio importante debe tener tests.

Priorizar tests para:

* relaciones;
* cálculos de mantenimiento;
* alertas;
* fechas;
* kilómetros;
* permisos;
* aislamiento de datos;
* exportaciones;
* operaciones críticas.

No escribir tests solamente para aumentar cobertura.

Los tests deben proteger comportamiento relevante.

---

# 37. Verificaciones obligatorias

Después de una modificación significativa ejecutar como mínimo:

python manage.py check

python manage.py test

Si se modificaron modelos:

python manage.py makemigrations --check

Corregir errores antes de finalizar.

---

# 38. HTMX

HTMX debe utilizarse cuando mejore claramente la experiencia.

Ejemplos:

* búsquedas;
* filtros;
* formularios parciales;
* modales;
* actualización de estados;
* cargar partes de una ficha.

No convertir toda la aplicación en una SPA artificial usando HTMX.

Los endpoints principales deben seguir funcionando de manera comprensible.

---

# 39. Bootstrap

Reutilizar componentes y estilos.

Evitar CSS personalizado para cosas que Bootstrap resuelve correctamente.

Cuando sea necesario CSS propio:

static/css/app.css

Mantenerlo organizado.

El diseño debe mantener una identidad consistente.

---

# 40. Diseño visual

La aplicación debe sentirse relacionada con motos/taller sin caer en una estética exagerada.

Preferir:

* interfaz moderna;
* alto contraste;
* jerarquía clara;
* cards;
* badges;
* estados visuales;
* iconografía sencilla.

La estética nunca debe perjudicar la legibilidad.

---

# 41. Funciones fuera del MVP

No agregar automáticamente:

* stock;
* facturación electrónica;
* ARCA;
* contabilidad;
* proveedores;
* pagos;
* marketplace;
* chat;
* red social;
* turnos online;
* IA;
* telemetría;
* geolocalización.

Estas funcionalidades sólo deben desarrollarse si el usuario las solicita explícitamente.

---

# 42. Multi-taller

Inicialmente existe un solo taller.

Sin embargo, evitar decisiones que hagan imposible soportar varios talleres en el futuro.

El concepto futuro puede ser:

Taller

├ Usuarios
├ Clientes
├ Motos
└ Servicios

No implementar todavía un sistema SaaS complejo.

No agregar aislamiento multi-tenant completo hasta que sea necesario.

Pero considerar esta futura posibilidad al diseñar relaciones importantes.

---

# 43. Backups

La información histórica del taller es crítica.

Debe existir progresivamente la posibilidad de exportar:

* clientes;
* motos;
* servicios;
* mantenimientos.

CSV y Excel.

Una exportación manual simple es preferible inicialmente a una infraestructura compleja de backups automáticos.

---

# 44. Git

Trabajar con cambios pequeños y coherentes.

No mezclar en el mismo cambio:

* refactors enormes;
* funcionalidades nuevas;
* cambios visuales no relacionados.

Nunca versionar:

* `.env`;
* secretos;
* credenciales;
* bases locales;
* `.venv`;
* archivos temporales.

---

# 45. Documentación

Mantener `/docs` actualizado cuando una decisión cambie significativamente.

Archivos principales:

docs/architecture.md
docs/data-model.md
docs/product-vision.md
docs/roadmap.md

No duplicar innecesariamente documentación entre archivos.

---

# 46. Flujo obligatorio para agentes

Antes de implementar una tarea:

1. Leer `AGENTS.md`.
2. Leer los archivos relevantes en `/docs`.
3. Inspeccionar el código existente relacionado.
4. Entender cómo funciona actualmente.
5. Identificar el cambio mínimo necesario.
6. Implementar respetando la arquitectura existente.
7. Crear o actualizar tests.
8. Ejecutar verificaciones.
9. Revisar el diff completo.
10. Informar claramente qué se modificó.

---

# 47. No asumir

No asumir que una funcionalidad no visible no existe.

Buscar primero en el repositorio.

Antes de crear:

* modelo;
* servicio;
* utilidad;
* template;
* helper;
* endpoint;

comprobar si ya existe algo equivalente.

Evitar duplicación.

---

# 48. Refactors

No hacer refactors grandes que no sean necesarios para cumplir la tarea solicitada.

Si durante una tarea se detecta deuda técnica no relacionada:

documentarla o mencionarla.

No modificar media aplicación sin autorización.

---

# 49. Compatibilidad

No romper comportamiento existente salvo que el requerimiento lo exija.

Antes de modificar una API interna, modelo o ruta:

buscar todas sus referencias.

---

# 50. Cuando haya dudas de arquitectura

Priorizar en este orden:

1. simplicidad;
2. integridad de datos;
3. seguridad;
4. experiencia de usuario;
5. mantenibilidad;
6. costos bajos;
7. rendimiento.

No sacrificar integridad o seguridad solamente para reducir unas pocas líneas de código.

---

# 51. Resultado esperado del proyecto

El producto debe terminar permitiendo que un mecánico pueda abrir la aplicación y rápidamente responder:

* ¿Quién es este cliente?
* ¿Qué moto tiene?
* ¿Qué se le hizo?
* ¿Cuándo se hizo?
* ¿A qué kilometraje?
* ¿Qué mantenimiento corresponde ahora?
* ¿Qué está por vencer?
* ¿Qué ya venció?
* ¿Ya contactamos al cliente?
* ¿Cómo lo contacto?
* ¿Qué debemos revisar cuando vuelva?

Si una funcionalidad ayuda directamente a responder alguna de estas preguntas, probablemente pertenece al núcleo del producto.

---

# 52. Regla final

No desarrollar tecnología por la tecnología misma.

Este sistema existe para hacer más fácil el trabajo cotidiano de un taller de motos.

Toda decisión técnica debe estar al servicio de ese objetivo.