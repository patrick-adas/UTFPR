from django.urls import reverse

from core.testing import BaseTestCase

from .models import User


class ContasTests(BaseTestCase):
    def test_paginas_exigem_login(self):
        resp = self.client.get(reverse("core:inicio"))
        self.assertRedirects(resp, f"{reverse('accounts:login')}?next=/")

    def test_login_com_usuario_e_senha(self):
        resp = self.client.post(reverse("accounts:login"), {"username": "ana", "password": "senha-forte-1"})
        self.assertRedirects(resp, reverse("core:inicio"))

    def test_colaborador_nao_acessa_equipe(self):
        self.entrar(self.ana)
        self.assertEqual(self.client.get(reverse("accounts:equipe")).status_code, 403)
        self.assertEqual(self.client.get(reverse("accounts:colaborador_novo")).status_code, 403)

    def test_proprietario_cria_colaborador_que_deve_trocar_senha(self):
        self.entrar(self.dono)
        resp = self.client.post(
            reverse("accounts:colaborador_novo"),
            {"first_name": "Carla", "username": "carla", "papel": "COLABORADOR", "senha_inicial": "Inicial#2026"},
        )
        self.assertRedirects(resp, reverse("accounts:equipe"))
        carla = User.objects.get(username="carla")
        self.assertTrue(carla.deve_trocar_senha)
        self.assertTrue(carla.check_password("Inicial#2026"))

        # No primeiro acesso, qualquer página leva à troca de senha
        self.client.force_login(carla)
        self.assertRedirects(self.client.get(reverse("core:inicio")), reverse("accounts:trocar_senha"))
        resp = self.client.post(
            reverse("accounts:trocar_senha"),
            {"old_password": "Inicial#2026", "new_password1": "Minha#Senha99", "new_password2": "Minha#Senha99"},
        )
        self.assertRedirects(resp, reverse("core:inicio"))
        carla.refresh_from_db()
        self.assertFalse(carla.deve_trocar_senha)
        self.assertEqual(self.client.get(reverse("core:inicio")).status_code, 200)

    def test_proprietario_nao_se_desativa(self):
        self.entrar(self.dono)
        self.client.post(reverse("accounts:colaborador_ativo", args=[self.dono.pk]))
        self.dono.refresh_from_db()
        self.assertTrue(self.dono.is_active)

    def test_desativar_colaborador(self):
        self.entrar(self.dono)
        self.client.post(reverse("accounts:colaborador_ativo", args=[self.ana.pk]))
        self.ana.refresh_from_db()
        self.assertFalse(self.ana.is_active)
