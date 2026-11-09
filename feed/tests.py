from django.urls import reverse

from core.testing import BaseTestCase

from .models import Curtida, Post


class FeedTests(BaseTestCase):
    def test_colaborador_publica_e_aparece_no_feed(self):
        self.entrar(self.ana)
        self.client.post(reverse("feed:postar"), {"texto": "Bom dia, equipe!"})
        self.assertTrue(Post.objects.filter(autor=self.ana, texto="Bom dia, equipe!").exists())
        self.entrar(self.bruno)
        self.assertContains(self.client.get(reverse("core:inicio")), "Bom dia, equipe!")

    def test_curtir_alterna(self):
        post = Post.objects.create(autor=self.ana, texto="Oi")
        self.entrar(self.bruno)
        url = reverse("feed:curtir", args=[post.pk])
        self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(Curtida.objects.count(), 1)
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(Curtida.objects.count(), 0)
        self.assertContains(resp, f'id="post-{post.pk}"')

    def test_so_autor_ou_proprietario_apagam(self):
        post = Post.objects.create(autor=self.ana, texto="Oi")
        self.entrar(self.bruno)
        self.assertEqual(self.client.post(reverse("feed:apagar", args=[post.pk])).status_code, 403)
        self.entrar(self.dono)
        self.client.post(reverse("feed:apagar", args=[post.pk]))
        self.assertFalse(Post.objects.exists())

    def test_so_proprietario_fixa(self):
        post = Post.objects.create(autor=self.ana, texto="Oi")
        self.entrar(self.ana)
        self.assertEqual(self.client.post(reverse("feed:fixar", args=[post.pk])).status_code, 403)
        self.entrar(self.dono)
        self.client.post(reverse("feed:fixar", args=[post.pk]))
        post.refresh_from_db()
        self.assertTrue(post.fixado)
