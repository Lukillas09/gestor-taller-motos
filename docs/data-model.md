# Modelo de datos

La Fase 1 implementa las entidades `Cliente` y `Moto`. Las entidades de servicios, mantenimientos y alertas continúan como conceptos futuros.

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

## Entidades futuras

- `Taller`: posible agrupación para soportar varios talleres en el futuro;
- `Usuario`: acceso mediante Django Auth;
- `Servicio`: ingreso u orden de trabajo con fecha, kilometraje, tareas y precios;
- `TipoMantenimiento`: definición de intervalos configurables;
- `MantenimientoRealizado`: registro de mantenimiento en una moto;
- `Seguimiento/Alerta`: estado de mantenimientos y contacto con clientes.

Estas entidades futuras no están implementadas en la Fase 1.
