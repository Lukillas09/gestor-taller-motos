import hashlib
import subprocess
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.core.management import call_command
from django.test import SimpleTestCase

from apps.exportaciones.backup import (
    BackupError,
    ResultadoBackup,
    crear_backup_postgres,
)


def conexion_postgres(*, vendor="postgresql", password="secreto-no-visible"):
    return SimpleNamespace(
        vendor=vendor,
        settings_dict={
            "NAME": "motoservice",
            "HOST": "db.example.test",
            "PORT": "5432",
            "USER": "motoservice_user",
            "PASSWORD": password,
            "OPTIONS": {"sslmode": "require"},
        },
    )


class BackupPostgresTests(SimpleTestCase):
    def _ruta_temporal(self):
        ruta = Path.cwd() / f".backup-test-{uuid4().hex}.dump"
        checksum = ruta.with_suffix(".dump.sha256")
        self.addCleanup(ruta.unlink, missing_ok=True)
        self.addCleanup(checksum.unlink, missing_ok=True)
        return ruta

    def _which(self, nombre):
        return str(Path("herramientas") / nombre)

    def test_rechaza_sqlite_sin_buscar_herramientas(self):
        with patch("apps.exportaciones.backup.shutil.which") as which:
            with self.assertRaisesMessage(
                BackupError,
                "requiere una conexión PostgreSQL",
            ):
                crear_backup_postgres(
                    conexion_postgres(vendor="sqlite"),
                    "backup.dump",
                )

        which.assert_not_called()

    def test_falla_si_pg_dump_no_esta_instalado(self):
        with patch("apps.exportaciones.backup.shutil.which", return_value=None):
            with self.assertRaisesMessage(BackupError, "No se encontró pg_dump"):
                crear_backup_postgres(conexion_postgres(), "backup.dump")

    def test_falla_si_pg_restore_no_esta_instalado(self):
        with patch(
            "apps.exportaciones.backup.shutil.which",
            side_effect=("pg_dump", None),
        ):
            with self.assertRaisesMessage(BackupError, "No se encontró pg_restore"):
                crear_backup_postgres(conexion_postgres(), "backup.dump")

    def test_no_sobrescribe_archivos_sin_force(self):
        salida = self._ruta_temporal()
        salida.write_bytes(b"anterior")
        with patch(
            "apps.exportaciones.backup.shutil.which",
            side_effect=self._which,
        ):
            with self.assertRaisesMessage(BackupError, "ya existen"):
                crear_backup_postgres(conexion_postgres(), salida)

        self.assertEqual(salida.read_bytes(), b"anterior")

    def test_error_de_pg_dump_elimina_archivo_parcial_y_no_crea_checksum(self):
        def ejecutar(argumentos, **kwargs):
            salida = Path(argumentos[argumentos.index("--file") + 1])
            salida.write_bytes(b"parcial")
            return subprocess.CompletedProcess(argumentos, 1, stderr="detalle privado")

        salida = self._ruta_temporal()
        with (
            patch(
                "apps.exportaciones.backup.shutil.which",
                side_effect=self._which,
            ),
            patch("apps.exportaciones.backup.subprocess.run", side_effect=ejecutar),
        ):
            with self.assertRaisesMessage(BackupError, "pg_dump no pudo"):
                crear_backup_postgres(conexion_postgres(), salida)

        self.assertFalse(salida.exists())
        self.assertFalse(salida.with_suffix(".dump.sha256").exists())

    def test_force_con_error_conserva_backup_anterior(self):
        salida = self._ruta_temporal()
        salida.write_bytes(b"backup-anterior")

        def ejecutar(argumentos, **kwargs):
            Path(argumentos[argumentos.index("--file") + 1]).write_bytes(b"parcial")
            return subprocess.CompletedProcess(argumentos, 1)

        with (
            patch(
                "apps.exportaciones.backup.shutil.which",
                side_effect=self._which,
            ),
            patch("apps.exportaciones.backup.subprocess.run", side_effect=ejecutar),
        ):
            with self.assertRaises(BackupError):
                crear_backup_postgres(conexion_postgres(), salida, force=True)

        self.assertEqual(salida.read_bytes(), b"backup-anterior")

    def test_rechaza_archivo_vacio(self):
        def ejecutar(argumentos, **kwargs):
            Path(argumentos[argumentos.index("--file") + 1]).touch()
            return subprocess.CompletedProcess(argumentos, 0)

        salida = self._ruta_temporal()
        with (
            patch(
                "apps.exportaciones.backup.shutil.which",
                side_effect=self._which,
            ),
            patch("apps.exportaciones.backup.subprocess.run", side_effect=ejecutar),
        ):
            with self.assertRaisesMessage(BackupError, "archivo de backup válido"):
                crear_backup_postgres(conexion_postgres(), salida)

        self.assertFalse(salida.exists())

    def test_validacion_fallida_elimina_dump_y_no_crea_checksum(self):
        def ejecutar(argumentos, **kwargs):
            if "--file" in argumentos:
                Path(argumentos[argumentos.index("--file") + 1]).write_bytes(b"dump")
                return subprocess.CompletedProcess(argumentos, 0)
            return subprocess.CompletedProcess(argumentos, 1, stderr="archivo inválido")

        salida = self._ruta_temporal()
        with (
            patch(
                "apps.exportaciones.backup.shutil.which",
                side_effect=self._which,
            ),
            patch("apps.exportaciones.backup.subprocess.run", side_effect=ejecutar),
        ):
            with self.assertRaisesMessage(BackupError, "no pudo validar"):
                crear_backup_postgres(conexion_postgres(), salida)

        self.assertFalse(salida.exists())
        self.assertFalse(salida.with_suffix(".dump.sha256").exists())

    def test_backup_correcto_usa_custom_public_ssl_shell_false_y_checksum(self):
        contenido = b"backup-postgresql-valido"

        def ejecutar(argumentos, **kwargs):
            if "--file" in argumentos:
                Path(argumentos[argumentos.index("--file") + 1]).write_bytes(contenido)
            return subprocess.CompletedProcess(argumentos, 0, stdout="OK", stderr="")

        salida = self._ruta_temporal()
        with (
            patch.dict(
                "os.environ",
                {"DATABASE_URL": "no-debe-heredarse", "SECRET_KEY": "no-heredar"},
            ),
            patch(
                "apps.exportaciones.backup.shutil.which",
                side_effect=self._which,
            ),
            patch(
                "apps.exportaciones.backup.subprocess.run",
                side_effect=ejecutar,
            ) as run,
        ):
            resultado = crear_backup_postgres(conexion_postgres(), salida)

        self.assertEqual(resultado.archivo, salida.resolve())
        self.assertEqual(resultado.tamanio, len(contenido))
        esperado = hashlib.sha256(contenido).hexdigest()
        self.assertEqual(resultado.sha256, esperado)
        self.assertEqual(
            resultado.checksum_archivo.read_text(encoding="ascii"),
            f"{esperado}  {salida.name}\n",
        )

        llamada_dump, llamada_restore = run.call_args_list
        argumentos_dump = llamada_dump.args[0]
        self.assertIn("--format=custom", argumentos_dump)
        self.assertIn("--schema=public", argumentos_dump)
        self.assertIn("--no-owner", argumentos_dump)
        self.assertIn("--no-acl", argumentos_dump)
        self.assertNotIn("secreto-no-visible", argumentos_dump)
        self.assertFalse(llamada_dump.kwargs["shell"])
        self.assertEqual(llamada_dump.kwargs["env"]["PGPASSWORD"], "secreto-no-visible")
        self.assertEqual(llamada_dump.kwargs["env"]["PGSSLMODE"], "require")
        self.assertNotIn("DATABASE_URL", llamada_dump.kwargs["env"])
        self.assertNotIn("SECRET_KEY", llamada_dump.kwargs["env"])
        self.assertEqual(llamada_restore.args[0][1], "--list")
        self.assertFalse(llamada_restore.kwargs["shell"])
        self.assertNotIn("PGPASSWORD", llamada_restore.kwargs["env"])

    def test_password_no_aparece_en_argumentos_ni_en_error(self):
        password = "password-super-secreto"
        argumentos_observados = []

        def ejecutar(argumentos, **kwargs):
            argumentos_observados.extend(argumentos)
            return subprocess.CompletedProcess(argumentos, 1, stderr=password)

        salida = self._ruta_temporal()
        with (
            patch(
                "apps.exportaciones.backup.shutil.which",
                side_effect=self._which,
            ),
            patch("apps.exportaciones.backup.subprocess.run", side_effect=ejecutar),
        ):
            with self.assertRaises(BackupError) as contexto:
                crear_backup_postgres(
                    conexion_postgres(password=password),
                    salida,
                )

        self.assertNotIn(password, " ".join(argumentos_observados))
        self.assertNotIn(password, str(contexto.exception))


class BackupCommandTests(SimpleTestCase):
    def test_comando_informa_resultado_sin_datos_de_conexion(self):
        salida_stdout = StringIO()
        archivo = Path("C:/Backups/motoservice.dump")
        resultado = ResultadoBackup(
            archivo=archivo,
            checksum_archivo=Path(f"{archivo}.sha256"),
            tamanio=2048,
            sha256="a" * 64,
        )

        with patch(
            "apps.exportaciones.management.commands.backup_database.crear_backup_postgres",
            return_value=resultado,
        ) as crear:
            call_command(
                "backup_database",
                output=str(archivo),
                stdout=salida_stdout,
            )

        crear.assert_called_once()
        contenido = salida_stdout.getvalue()
        self.assertIn("Backup PostgreSQL creado correctamente", contenido)
        self.assertIn("Verificación pg_restore: OK", contenido)
        self.assertIn("2.0 KB", contenido)
        self.assertNotIn("PGPASSWORD", contenido)
        self.assertNotIn("DATABASE_URL", contenido)
