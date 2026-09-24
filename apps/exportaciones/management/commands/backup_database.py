from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from apps.exportaciones.backup import (
    BackupError,
    crear_backup_postgres,
    tamanio_legible,
)
from apps.exportaciones.utils import momento_local


class Command(BaseCommand):
    help = "Crea un backup manual del schema PostgreSQL de MotoService usando pg_dump."

    def add_arguments(self, parser):
        destino = parser.add_mutually_exclusive_group()
        destino.add_argument(
            "--output",
            help="Ruta completa del archivo .dump que se generará.",
        )
        destino.add_argument(
            "--output-dir",
            help="Directorio donde se creará el backup con nombre automático.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Permite reemplazar un backup y checksum existentes.",
        )

    def handle(self, *args, **options):
        marca_tiempo = momento_local()
        nombre = f"motoservice_{marca_tiempo:%Y-%m-%d_%H%M%S}.dump"
        if options.get("output"):
            salida = Path(options["output"])
        elif options.get("output_dir"):
            salida = Path(options["output_dir"]) / nombre
        else:
            salida = Path.cwd() / "backups" / nombre

        self.stdout.write("Creando backup PostgreSQL...")
        try:
            resultado = crear_backup_postgres(
                connection,
                salida,
                force=options["force"],
            )
        except BackupError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(self.style.SUCCESS("Backup PostgreSQL creado correctamente."))
        self.stdout.write(f"Archivo: {resultado.archivo}")
        self.stdout.write(f"Tamaño: {tamanio_legible(resultado.tamanio)}")
        self.stdout.write("Verificación pg_restore: OK")
        self.stdout.write(f"SHA-256: {resultado.sha256}")
        self.stdout.write(f"Checksum: {resultado.checksum_archivo}")
