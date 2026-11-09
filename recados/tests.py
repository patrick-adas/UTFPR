from django.urls import reverse

from core.testing import BaseTestCase

from .models import Leitura, Recado


class RecadosTests(BaseTestCase):
    def test_colaborador_nao_cria_recado(self):
        self.entrar(self.ana)
        resp = self.client.post(reverse("recados:novo"), {"titulo": "x", "texto": "y", "tipo": "GERAL"})
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Recado.objects.exists())

    def test_recado_privado_so_para_destinatario(self):
        self.entrar(self.dono)
        self.client.post(
            reverse("recados:novo"),
            {"titulo": "Só para a Ana", "texto": "Conversa reservada", "tipo": "PRIVADO", "destinatarios": [self.ana.pk]},
        )
        recado = Recado.objects.get()
        self.entrar(self.ana)
        self.assertContains(self.client.get(reverse("recados:lista")), "Só para a Ana")
        self.assertEqual(self.client.get(reverse("recados:detalhe", args=[recado.pk])).status_code, 200)
        self.entrar(self.bruno)
        self.assertNotContains(self.client.get(reverse("recados:lista")), "Só para a Ana")
        self.assertNotContains(self.client.get(reverse("core:inicio")), "Só para a Ana")
        self.assertEqual(self.client.get(reverse("recados:detalhe", args=[recado.pk])).status_code, 404)

    def test_privado_exige_destinatario(self):
        self.entrar(self.dono)
        self.client.post(reverse("recados:novo"), {"titulo": "x", "texto": "y", "tipo": "PRIVADO"})
        self.assertFalse(Recado.objects.exists())

    def test_abrir_recado_confirma_leitura(self):
        recado = Recado.objects.create(autor=self.dono, titulo="Geral", texto="Para todos")
        self.assertEqual(Recado.objects.nao_lidos_por(self.ana).count(), 1)
        self.entrar(self.ana)
        self.client.get(reverse("recados:detalhe", args=[recado.pk]))
        self.assertTrue(Leitura.objects.filter(recado=recado, usuario=self.ana).exists())
        self.assertEqual(Recado.objects.nao_lidos_por(self.ana).count(), 0)
        self.entrar(self.dono)
        resp = self.client.get(reverse("recados:detalhe", args=[recado.pk]))
        self.assertContains(resp, "Ainda não leu")  # Bruno
        self.assertContains(resp, "Lido ")  # Ana
