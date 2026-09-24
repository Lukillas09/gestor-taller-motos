import hashlib
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


SCHEMA_APLICACION = "public"


class BackupError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ResultadoBackup:
    archivo: Path
    checksum_archivo: Path
    tamanio: int
    sha256: str


def _entorno_postgres(settings_dict):
    nombre = str(settings_dict.get("NAME") or "").strip()
    if not nombre:
        raise BackupError("La conexión PostgreSQL no tiene una base configurada.")

    entorno = os.environ.copy()
    entorno.pop("DATABASE_URL", None)
    entorno.pop("SECRET_KEY", None)
    valores = {
        "PGDATABASE": nombre,
        "PGHOST": settings_dict.get("HOST"),
        "PGPORT": settings_dict.get("PORT"),
        "PGUSER": settings_dict.get("USER"),
        "PGPASSWORD": settings_dict.get("PASSWORD"),
        "PGSSLMODE": (settings_dict.get("OPTIONS") or {}).get("sslmode"),
    }
    for clave in valores:
        entorno.pop(clave, None)
    for clave, valor in valores.items():
        if valor not in (None, ""):
            entorno[clave] = str(valor)
    return entorno


def _eliminar_si_existe(ruta):
    try:
        ruta.unlink(missing_ok=True)
    except OSError:
        pass


def calcular_sha256(ruta):
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def crear_backup_postgres(connection, output, *, force=False):
    if connection.vendor != "postgresql":
        raise BackupError("El backup PostgreSQL requiere una conexión PostgreSQL.")

    pg_dump = shutil.which("pg_dump")
    if not pg_dump:
        raise BackupError(
            "No se encontró pg_dump. Instalá las herramientas cliente de PostgreSQL."
        )
    pg_restore = shutil.which("pg_restore")
    if not pg_restore:
        raise BackupError(
            "No se encontró pg_restore. Instalá las herramientas cliente de PostgreSQL."
        )

    destino = Path(output).expanduser().resolve()
    if destino.suffix.lower() != ".dump":
        raise BackupError("El archivo de salida debe usar la extensión .dump.")
    checksum_archivo = destino.with_suffix(destino.suffix + ".sha256")
    if not force and (destino.exists() or checksum_archivo.exists()):
        raise BackupError(
            "El backup o su checksum ya existen. Elegí otro nombre o usá --force."
        )

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise BackupError("No se pudo crear el directorio de destino.") from error

    identificador_temporal = uuid4().hex
    destino_temporal = destino.with_name(
        f".{destino.name}.{identificador_temporal}.partial"
    )
    checksum_temporal = checksum_archivo.with_name(
        f".{checksum_archivo.name}.{identificador_temporal}.partial"
    )
    entorno = _entorno_postgres(connection.settings_dict)
    comando_dump = [
        pg_dump,
        "--format=custom",
        f"--schema={SCHEMA_APLICACION}",
        "--no-owner",
        "--no-acl",
        "--file",
        str(destino_temporal),
    ]

    try:
        resultado_dump = subprocess.run(
            comando_dump,
            env=entorno,
            capture_output=True,
            text=True,
            shell=False,
        )
    except OSError as error:
        _eliminar_si_existe(destino_temporal)
        raise BackupError("No se pudo ejecutar pg_dump.") from error

    if resultado_dump.returncode != 0:
        _eliminar_si_existe(destino_temporal)
        _eliminar_si_existe(checksum_temporal)
        raise BackupError(
            "pg_dump no pudo crear el backup. Revisá la conexión y los permisos."
        )
    if not destino_temporal.is_file() or destino_temporal.stat().st_size <= 0:
        _eliminar_si_existe(destino_temporal)
        _eliminar_si_existe(checksum_temporal)
        raise BackupError("pg_dump no generó un archivo de backup válido.")

    entorno_restore = entorno.copy()
    entorno_restore.pop("PGPASSWORD", None)
    try:
        resultado_restore = subprocess.run(
            [pg_restore, "--list", str(destino_temporal)],
            env=entorno_restore,
            capture_output=True,
            text=True,
            shell=False,
        )
    except OSError as error:
        _eliminar_si_existe(destino_temporal)
        raise BackupError("No se pudo ejecutar pg_restore para validar el backup.") from error

    if resultado_restore.returncode != 0:
        _eliminar_si_existe(destino_temporal)
        _eliminar_si_existe(checksum_temporal)
        raise BackupError("pg_restore no pudo validar el archivo generado.")

    try:
        checksum = calcular_sha256(destino_temporal)
        checksum_temporal.write_text(
            f"{checksum}  {destino.name}\n",
            encoding="ascii",
        )
        destino_temporal.replace(destino)
        checksum_temporal.replace(checksum_archivo)
        tamanio = destino.stat().st_size
    except OSError as error:
        _eliminar_si_existe(destino_temporal)
        _eliminar_si_existe(checksum_temporal)
        raise BackupError("No se pudo generar el checksum del backup.") from error

    return ResultadoBackup(
        archivo=destino,
        checksum_archivo=checksum_archivo,
        tamanio=tamanio,
        sha256=checksum,
    )


def tamanio_legible(cantidad_bytes):
    valor = float(cantidad_bytes)
    for unidad in ("B", "KB", "MB", "GB", "TB"):
        if valor < 1024 or unidad == "TB":
            return f"{valor:.1f} {unidad}"
        valor /= 1024
