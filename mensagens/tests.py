from django.urls import reverse

from core.testing import BaseTestCase

from .models import Conversa, Mensagem, total_nao_lidas


class MensagensTests(BaseTestCase):
    def test_iniciar_reaproveita_conversa(self):
        self.entrar(self.ana)
        self.client.get(reverse("mensagens:iniciar", args=[self.bruno.pk]))
        self.client.get(reverse("mensagens:iniciar", args=[self.bruno.pk]))
        self.assertEqual(Conversa.objects.count(), 1)
        self.entrar(self.bruno)
        self.client.get(reverse("mensagens:iniciar", args=[self.ana.pk]))
        self.assertEqual(Conversa.objects.count(), 1)

    def test_conversa_inacessivel_para_terceiros(self):
        conversa = Conversa.obter_ou_criar(self.ana, self.bruno)
        Mensagem.objects.create(conversa=conversa, autor=self.ana, texto="segredo")
        self.entrar(self.dono)
        self.assertEqual(self.client.get(reverse("mensagens:conversa", args=[conversa.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("mensagens:novas", args=[conversa.pk])).status_code, 404)
        resp = self.client.post(reverse("mensagens:enviar", args=[conversa.pk]), {"texto": "intruso"})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(conversa.mensagens.count(), 1)

    def test_enviar_via_htmx_dispara_evento(self):
        conversa = Conversa.obter_ou_criar(self.ana, self.bruno)
        self.entrar(self.ana)
        resp = self.client.post(reverse("mensagens:enviar", args=[conversa.pk]), {"texto": "Oi!"}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp["HX-Trigger"], "mensagemEnviada")
        self.assertEqual(conversa.mensagens.get().texto, "Oi!")

    def test_polling_retorna_so_mensagens_novas(self):
        conversa = Conversa.obter_ou_criar(self.ana, self.bruno)
        antiga = Mensagem.objects.create(conversa=conversa, autor=self.ana, texto="mensagem antiga")
        nova = Mensagem.objects.create(conversa=conversa, autor=self.ana, texto="mensagem nova")
        self.entrar(self.bruno)
        resp = self.client.get(reverse("mensagens:novas", args=[conversa.pk]), {"depois": antiga.pk})
        self.assertContains(resp, "mensagem nova")
        self.assertNotContains(resp, "mensagem antiga")
        # O próximo poller já aponta para a última mensagem recebida
        self.assertContains(resp, f"depois={nova.pk}")

    def test_contagem_de_nao_lidas(self):
        conversa = Conversa.obter_ou_criar(self.ana, self.bruno)
        Mensagem.objects.create(conversa=conversa, autor=self.ana, texto="1")
        Mensagem.objects.create(conversa=conversa, autor=self.ana, texto="2")
        self.assertEqual(total_nao_lidas(self.bruno), 2)
        self.assertEqual(total_nao_lidas(self.ana), 0)
        self.entrar(self.bruno)
        self.client.get(reverse("mensagens:conversa", args=[conversa.pk]))
        self.assertEqual(total_nao_lidas(self.bruno), 0)
        resp = self.client.get(reverse("core:contadores"))
        self.assertContains(resp, 'id="badge-mensagens"')
