import json
import tempfile
from decimal import Decimal
from pathlib import Path

from django.test import override_settings
from django.urls import reverse

from core.templatetags.farmacia import valor_meta

from .testing import BaseTestCase


class CoreTests(BaseTestCase):
    def test_inicio_mostra_widgets(self):
        self.entrar(self.ana)
        resp = self.client.get(reverse("core:inicio"))
        self.assertContains(resp, "Minhas tarefas")
        self.assertContains(resp, "Meta da farmácia")

    def test_manifest_e_service_worker(self):
        resp = self.client.get(reverse("core:manifest"))
        self.assertEqual(resp["Content-Type"], "application/manifest+json")
        manifest = json.loads(resp.content)
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(len(manifest["icons"]), 3)
        sw = self.client.get("/sw.js")
        self.assertEqual(sw.status_code, 200)
        self.assertIn("javascript", sw["Content-Type"])

    def test_media_exige_login_e_bloqueia_path_traversal(self):
        with tempfile.TemporaryDirectory() as pasta, override_settings(MEDIA_ROOT=pasta):
            Path(pasta, "fotos").mkdir()
            Path(pasta, "fotos", "a.png").write_bytes(b"png")
            self.assertEqual(self.client.get("/media/fotos/a.png").status_code, 302)
            self.entrar(self.ana)
            resp = self.client.get("/media/fotos/a.png")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(b"".join(resp.streaming_content), b"png")
            self.assertEqual(self.client.get("/media/../farmacia/settings.py").status_code, 404)

    def test_formatacao_valores(self):
        self.assertEqual(valor_meta(Decimal("1234.5"), "R$"), "R$ 1.234,50")
        self.assertEqual(valor_meta(Decimal("30"), "atendimentos"), "30 atendimentos")
