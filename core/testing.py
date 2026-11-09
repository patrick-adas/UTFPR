from django.test import TestCase

from accounts.models import User


class BaseTestCase(TestCase):
    """Cria um proprietário e dois colaboradores para os testes."""

    @classmethod
    def setUpTestData(cls):
        cls.dono = User.objects.create_user("dono", password="senha-forte-1", papel=User.Papel.PROPRIETARIO, first_name="Dona")
        cls.ana = User.objects.create_user("ana", password="senha-forte-1", first_name="Ana")
        cls.bruno = User.objects.create_user("bruno", password="senha-forte-1", first_name="Bruno")

    def entrar(self, user):
        self.client.force_login(user)
