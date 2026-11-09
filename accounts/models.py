from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Papel(models.TextChoices):
        PROPRIETARIO = "PROPRIETARIO", "Proprietário"
        COLABORADOR = "COLABORADOR", "Colaborador"

    papel = models.CharField(max_length=20, choices=Papel.choices, default=Papel.COLABORADOR)
    cargo = models.CharField("cargo", max_length=80, blank=True, help_text="Ex.: Farmacêutico, Balconista, Caixa")
    foto = models.ImageField(upload_to="fotos/", blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    deve_trocar_senha = models.BooleanField(
        default=False, help_text="Obriga a troca de senha no próximo acesso."
    )

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ["first_name", "username"]

    def __str__(self):
        return self.nome_exibicao

    @property
    def is_proprietario(self):
        return self.papel == self.Papel.PROPRIETARIO

    @property
    def nome_exibicao(self):
        return self.get_full_name() or self.username

    @property
    def iniciais(self):
        partes = self.nome_exibicao.split()
        if len(partes) >= 2:
            return (partes[0][0] + partes[-1][0]).upper()
        return self.nome_exibicao[:2].upper()
