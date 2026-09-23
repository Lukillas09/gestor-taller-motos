# Modelo de datos conceptual

En esta fase no se crean modelos de negocio. Las entidades futuras se documentan solo como guia conceptual.

## Taller

Representa el taller que utiliza el sistema. Inicialmente habra un unico taller, pero podria permitir reutilizar el sistema para otros talleres en el futuro.

## Usuario

Persona que accede a la aplicacion mediante Django Auth.

## Cliente

Persona propietaria o responsable de una o mas motos. Podra tener telefono, email, direccion y observaciones.

## Moto

Vehiculo asociado a un cliente. Podra incluir patente, marca, modelo, ano, cilindrada, kilometraje, numero de motor, numero de chasis y observaciones.

## Servicio

Ingreso u orden de trabajo del taller. Podra registrar kilometraje, trabajos realizados, precios y observaciones.

## TipoMantenimiento

Define mantenimientos recurrentes, como aceite, filtros, frenos, cadena, refrigerante o bujias.

## MantenimientoRealizado

Registra que un tipo de mantenimiento fue realizado en una moto, con fecha y kilometraje.

## Seguimiento/Alerta

Representa mantenimientos proximos o vencidos y el estado de contacto con el cliente.
