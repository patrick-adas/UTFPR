from decimal import Decimal

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from core.testing import BaseTestCase
from core.utils import inicio_do_mes, mes_anterior

from .models import Lancamento, MetaMensal


class MetasTests(BaseTestCase):
    def setUp(self):
        self.mes = inicio_do_mes()
        self.farmacia = MetaMensal.objects.create(titulo="Faturamento", mes=self.mes, valor_alvo=Decimal("1000"), unidade="R$")
        self.da_ana = MetaMensal.objects.create(
            titulo="Atendimentos da Ana", mes=self.mes, valor_alvo=Decimal("50"), unidade="atendimentos",
            escopo=MetaMensal.Escopo.INDIVIDUAL, responsavel=self.ana,
        )

    def test_valor_atual_e_percentual(self):
        hoje = timezone.localdate()
        Lancamento.objects.create(meta=self.farmacia, valor=Decimal("250"), data=hoje)
        Lancamento.objects.create(meta=self.farmacia, valor=Decimal("125.50"), data=hoje)
        self.assertEqual(self.farmacia.valor_atual, Decimal("375.50"))
        self.assertEqual(self.farmacia.percentual, 37.5)
        anotada = MetaMensal.objects.com_progresso().get(pk=self.farmacia.pk)
        self.assertEqual(anotada.valor_atual, Decimal("375.50"))
        self.assertFalse(anotada.atingida)
        Lancamento.objects.create(meta=self.farmacia, valor=Decimal("800"), data=hoje)
        self.assertTrue(self.farmacia.atingida)
        self.assertEqual(self.farmacia.percentual_barra, 100)

    def test_sem_lancamentos_percentual_zero(self):
        self.assertEqual(MetaMensal.objects.com_progresso().get(pk=self.farmacia.pk).percentual, 0)

    def test_colaborador_ve_meta_da_farmacia_e_as_proprias(self):
        self.entrar(self.ana)
        resp = self.client.get(reverse("metas:lista"))
        self.assertContains(resp, "Faturamento")
        self.assertContains(resp, "Atendimentos da Ana")
        self.entrar(self.bruno)
        resp = self.client.get(reverse("metas:lista"))
        self.assertContains(resp, "Faturamento")
        self.assertNotContains(resp, "Atendimentos da Ana")
        self.assertEqual(self.client.get(reverse("metas:detalhe", args=[self.da_ana.pk])).status_code, 404)

    def test_colaborador_nao_cria_meta(self):
        self.entrar(self.ana)
        self.assertEqual(self.client.get(reverse("metas:nova")).status_code, 403)

    def test_proprietario_cria_meta_individual(self):
        self.entrar(self.dono)
        resp = self.client.post(
            reverse("metas:nova"),
            {"titulo": "Genéricos", "mes": self.mes.strftime("%Y-%m"), "escopo": "INDIVIDUAL",
             "responsavel": self.bruno.pk, "valor_alvo": "300", "unidade": "unidades"},
        )
        self.assertEqual(resp.status_code, 302)
        meta = MetaMensal.objects.get(titulo="Genéricos")
        self.assertEqual(meta.responsavel, self.bruno)
        self.assertEqual(meta.mes, self.mes)

    def test_meta_individual_exige_responsavel(self):
        self.entrar(self.dono)
        self.client.post(
            reverse("metas:nova"),
            {"titulo": "Sem dono", "mes": self.mes.strftime("%Y-%m"), "escopo": "INDIVIDUAL", "valor_alvo": "10", "unidade": "un"},
        )
        self.assertFalse(MetaMensal.objects.filter(titulo="Sem dono").exists())

    def test_meta_da_farmacia_ignora_responsavel(self):
        self.entrar(self.dono)
        self.client.post(
            reverse("metas:nova"),
            {"titulo": "Clientes", "mes": self.mes.strftime("%Y-%m"), "escopo": "FARMACIA",
             "responsavel": self.ana.pk, "valor_alvo": "10", "unidade": "clientes"},
        )
        self.assertIsNone(MetaMensal.objects.get(titulo="Clientes").responsavel)

    def test_colaborador_lanca_so_na_propria_meta_individual(self):
        dados = {"valor": "5", "data": timezone.localdate().isoformat()}
        self.entrar(self.ana)
        self.client.post(reverse("metas:detalhe", args=[self.da_ana.pk]), dados)
        self.assertEqual(self.da_ana.lancamentos.count(), 1)
        resp = self.client.post(reverse("metas:detalhe", args=[self.farmacia.pk]), dados)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(self.farmacia.lancamentos.count(), 0)

    @override_settings(COLABORADOR_PODE_LANCAR=False)
    def test_configuracao_bloqueia_lancamento_do_colaborador(self):
        self.entrar(self.ana)
        resp = self.client.post(reverse("metas:detalhe", args=[self.da_ana.pk]), {"valor": "5", "data": timezone.localdate().isoformat()})
        self.assertEqual(resp.status_code, 403)

    def test_copiar_mes_anterior(self):
        anterior = mes_anterior(self.mes)
        MetaMensal.objects.create(titulo="Antiga", mes=anterior, valor_alvo=Decimal("10"), unidade="un")
        self.entrar(self.dono)
        self.client.post(reverse("metas:copiar_mes_anterior"), {"mes": self.mes.strftime("%Y-%m")})
        self.assertTrue(MetaMensal.objects.filter(titulo="Antiga", mes=self.mes).exists())
        # Rodar de novo não duplica
        self.client.post(reverse("metas:copiar_mes_anterior"), {"mes": self.mes.strftime("%Y-%m")})
        self.assertEqual(MetaMensal.objects.filter(titulo="Antiga", mes=self.mes).count(), 1)
