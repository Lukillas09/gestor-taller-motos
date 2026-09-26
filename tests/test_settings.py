import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase

from config.settings.base import env_bool


class DevelopmentStaticFilesTests(SimpleTestCase):
    def test_booleanos_reconocen_valores_explicitos_y_respetan_default(self):
        for value, default, expected in (
            (" True ", False, True),
            ("1", False, True),
            ("false", True, False),
            ("0", True, False),
            ("release", True, True),
            ("release", False, False),
        ):
            with self.subTest(value=value, default=default):
                with patch.dict(os.environ, {"TEST_BOOLEAN_SETTING": value}):
                    self.assertEqual(env_bool("TEST_BOOLEAN_SETTING", default), expected)

    def test_desarrollo_siempre_admite_hosts_locales(self):
        environment = os.environ.copy()
        environment.update(
            DJANGO_SETTINGS_MODULE="config.settings.development",
            ALLOWED_HOSTS="gestor-taller-motos-production.up.railway.app",
            DATABASE_URL="sqlite:///:memory:",
        )
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import json
import django
django.setup()
from django.conf import settings
print(json.dumps(settings.ALLOWED_HOSTS))
""",
            ],
            cwd=Path(settings.BASE_DIR),
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        allowed_hosts = json.loads(result.stdout)

        self.assertIn("gestor-taller-motos-production.up.railway.app", allowed_hosts)
        self.assertIn("localhost", allowed_hosts)
        self.assertIn("127.0.0.1", allowed_hosts)

    def probe_runserver(self, django_debug=None, legacy_debug="release"):
        environment = os.environ.copy()
        environment.update(
            DJANGO_SETTINGS_MODULE="config.settings.development",
            DEBUG=legacy_debug,
            DJANGO_DEBUG=django_debug or "",
            DATABASE_URL="sqlite:///:memory:",
        )
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import json
import django
django.setup()
from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import Command
from django.test import RequestFactory

handler = Command().get_handler(use_static_handler=True, insecure_serving=False)
responses = {}
for path in ('css/app.css', 'icons/ui.svg', 'icons/motoservice-mark-96.png'):
    headers = []
    request = RequestFactory().get('/static/' + path, HTTP_HOST='127.0.0.1')
    response = handler(request.environ, lambda status, values: headers.append((status, values)))
    try:
        body = b''.join(response)
        status, values = headers[0]
        responses[path] = {'status': status, 'content_type': dict(values)['Content-Type'], 'length': len(body)}
    finally:
        response.close()
print(json.dumps({'debug': settings.DEBUG, 'responses': responses}))
""",
            ],
            cwd=Path(settings.BASE_DIR),
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        return json.loads(result.stdout)

    def test_runserver_sirve_css_iconos_e_imagenes_con_debug_release_heredado(self):
        result = self.probe_runserver()

        self.assertTrue(result["debug"])
        for path, content_type in (
            ("css/app.css", "text/css"),
            ("icons/ui.svg", "image/svg+xml"),
            ("icons/motoservice-mark-96.png", "image/png"),
        ):
            with self.subTest(path=path):
                response = result["responses"][path]
                self.assertEqual(response["status"], "200 OK")
                self.assertEqual(response["content_type"], content_type)
                self.assertGreater(response["length"], 0)

    def test_debug_false_explicito_se_respeta_y_django_debug_tiene_prioridad(self):
        for django_debug, legacy_debug, expected in (
            (None, "False", False),
            ("False", "True", False),
            ("True", "False", True),
        ):
            with self.subTest(django_debug=django_debug, legacy_debug=legacy_debug):
                result = self.probe_runserver(django_debug, legacy_debug)
                self.assertEqual(result["debug"], expected)
