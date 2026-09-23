# Modelo de datos

Las Fases 1 y 2 implementan clientes, motos, servicios y los trabajos de mantenimiento realizados. Los intervalos, próximos vencimientos y alertas continúan reservados para la Fase 3.

## Cliente

Representa a la persona propietaria o responsable de una o más motos.

Campos:

- `nombre`: texto obligatorio, con espacios internos normalizados;
- `apellido`: texto opcional;
- `telefono`: texto opcional, sin restricción de unicidad;
- `email`: email opcional, validado por Django y no único;
- `direccion`: texto opcional;
- `observaciones`: texto opcional;
- `activo`: estado para archivado lógico;
- `creado_en` y `actualizado_en`: fechas de auditoría automáticas.

El orden predeterminado es por apellido y nombre. Un cliente archivado no aparece en el listado activo, pero continúa disponible en su ficha y puede restaurarse.

## Moto

Representa una moto vinculada a un cliente.

Campos:

- `cliente`: relación obligatoria con `Cliente` mediante `ForeignKey`;
- `patente`: texto opcional y único cuando existe;
- `marca` y `modelo`: textos obligatorios;
- `anio`: entero opcional entre 1900 y el año actual más uno;
- `cilindrada_cc`: entero positivo opcional expresado en cc;
- `color`: texto opcional;
- `kilometraje_actual`: último kilometraje conocido por el taller, entero positivo opcional;
- `numero_chasis` y `numero_motor`: textos opcionales;
- `observaciones`: texto opcional;
- `activo`: estado para archivado lógico;
- `creado_en` y `actualizado_en`: fechas de auditoría automáticas.

La patente se normaliza en el modelo: se convierte a mayúsculas y se eliminan espacios y guiones. Una patente vacía se guarda como `NULL`, lo que permite registrar varias motos sin patente. El orden predeterminado es por marca y modelo.

## Relación Cliente → Moto

La relación es uno a muchos:

```text
Cliente 1 ─── N Moto
```

Se utiliza `related_name="motos"`, por lo que las motos se consultan con `cliente.motos.all()`. La relación usa `on_delete=PROTECT`: no se puede borrar físicamente un cliente que tenga motos asociadas.

El archivado de un cliente no modifica sus motos. Las motos conservan explícitamente su estado activo o archivado y siguen accesibles desde sus propias fichas. Para agregar una moto nueva a un cliente archivado primero se debe restaurar al cliente.

## Servicio

Representa una visita o trabajo efectuado sobre una moto.

Campos principales:

- `moto`: relación protegida con la moto y no modificable después del alta;
- `cliente`: relación protegida que conserva al propietario existente al crear el servicio;
- `fecha`: fecha del trabajo, con soporte para carga histórica;
- `kilometraje`: lectura opcional de esa visita;
- `estado`: `ABIERTO`, `FINALIZADO` o `CANCELADO`;
- `trabajos_adicionales` y `observaciones`: detalle libre;
- `precio_total`: decimal opcional y no negativo;
- `creado_por`: usuario de Django que registró el servicio, conservado mientras exista;
- `creado_en` y `actualizado_en`: fechas de auditoría.

Un servicio nuevo toma su cliente desde `moto.cliente` en el servidor. Ese dato no cambia si la moto se transfiere posteriormente. Solo se admiten servicios nuevos para una moto activa cuyo cliente actual también esté activo.

Un kilometraje mayor actualiza `Moto.kilometraje_actual`. Un valor menor requiere confirmación explícita en el formulario y queda guardado como lectura histórica, sin reducir el último kilometraje conocido. Los servicios cancelados se conservan y nunca actualizan ese valor.

## TipoMantenimiento

Es el catálogo configurable de trabajos que el taller puede seleccionar al registrar un servicio. Contiene nombre, descripción, estado activo y fechas de auditoría. Desactivar un tipo lo oculta de servicios nuevos, pero mantiene su nombre visible y disponible dentro de los servicios históricos que ya lo utilizaron.

La Fase 2 carga un catálogo inicial de once trabajos habituales. Todavía no define intervalos de tiempo, kilómetros ni alertas.

## MantenimientoRealizado

Relaciona un `Servicio` con un `TipoMantenimiento` y permite observaciones. La combinación de servicio y tipo es única, por lo que el mismo trabajo no puede registrarse dos veces en una visita.

```text
Cliente 1 ─── N Moto
Cliente 1 ─── N Servicio (propietario histórico)
Moto 1 ─── N Servicio
Servicio 1 ─── N MantenimientoRealizado N ─── 1 TipoMantenimiento
```

La relación desde servicio hacia sus trabajos usa `CASCADE` porque son parte del propio registro. Las relaciones históricas hacia moto, cliente y tipo de mantenimiento usan `PROTECT`.

## Entidades futuras

- `Taller`: posible agrupación para soportar varios talleres en el futuro;
- `Usuario`: acceso mediante Django Auth;
- reglas configurables de intervalos por tiempo y kilometraje;
- `Seguimiento/Alerta`: estado de mantenimientos y contacto con clientes.
