import datetime

from django.urls import reverse
from django.utils import timezone

from core.testing import BaseTestCase

from .models import Tarefa


class TarefasTests(BaseTestCase):
    def test_colaborador_nao_cria_tarefa(self):
        self.entrar(self.ana)
        self.assertEqual(self.client.get(reverse("tarefas:nova")).status_code, 403)
        resp = self.client.post(reverse("tarefas:nova"), {"titulo": "x", "responsavel": self.ana.pk, "prioridade": 2, "status": "PENDENTE"})
        self.assertEqual(resp.status_code, 403)

    def test_proprietario_atribui_e_colaborador_conclui(self):
        self.entrar(self.dono)
        self.client.post(
            reverse("tarefas:nova"),
            {"titulo": "Conferir validade", "responsavel": self.ana.pk, "prioridade": 3, "status": "PENDENTE"},
        )
        tarefa = Tarefa.objects.get()
        self.assertEqual(tarefa.criada_por, self.dono)

        self.entrar(self.ana)
        self.assertContains(self.client.get(reverse("tarefas:lista")), "Conferir validade")
        self.client.post(reverse("tarefas:mudar_status", args=[tarefa.pk]), {"status": "CONCLUIDA"})
        tarefa.refresh_from_db()
        self.assertEqual(tarefa.status, Tarefa.Status.CONCLUIDA)
        self.assertIsNotNone(tarefa.concluida_em)

    def test_colaborador_nao_ve_tarefa_de_outro(self):
        tarefa = Tarefa.objects.create(titulo="Da Ana", responsavel=self.ana, criada_por=self.dono)
        self.entrar(self.bruno)
        self.assertNotContains(self.client.get(reverse("tarefas:lista")), "Da Ana")
        self.assertEqual(self.client.get(reverse("tarefas:detalhe", args=[tarefa.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("tarefas:mudar_status", args=[tarefa.pk]), {"status": "CONCLUIDA"}).status_code, 404)

    def test_tarefa_atrasada(self):
        ontem = timezone.localdate() - datetime.timedelta(days=1)
        tarefa = Tarefa(titulo="x", responsavel=self.ana, prazo=ontem)
        self.assertTrue(tarefa.atrasada)
        tarefa.status = Tarefa.Status.CONCLUIDA
        self.assertFalse(tarefa.atrasada)

    def test_next_externo_e_ignorado(self):
        tarefa = Tarefa.objects.create(titulo="x", responsavel=self.ana)
        self.entrar(self.ana)
        resp = self.client.post(
            reverse("tarefas:mudar_status", args=[tarefa.pk]), {"status": "CONCLUIDA", "next": "https://malicioso.example/"}
        )
        self.assertRedirects(resp, reverse("tarefas:lista"))
