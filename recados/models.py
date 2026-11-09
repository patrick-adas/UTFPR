from django.conf import settings
from django.db import models
from django.db.models import Q


class RecadoQuerySet(models.QuerySet):
    def visiveis_para(self, user):
        """Recados gerais + privados em que o usuário é destinatário (ou autor)."""
        if user.is_proprietario:
            return self.all()
        return self.filter(
            Q(tipo=Recado.Tipo.GERAL) | Q(destinatarios=user) | Q(autor=user)
        ).distinct()

    def nao_lidos_por(self, user):
        return self.visiveis_para(user).exclude(autor=user).exclude(leituras__usuario=user)


class Recado(models.Model):
    class Tipo(models.TextChoices):
        GERAL = "GERAL", "Geral (toda a equipe)"
        PRIVADO = "PRIVADO", "Privado"

    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recados_enviados")
    titulo = models.CharField("título", max_length=150)
    texto = models.TextField()
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.GERAL)
    destinatarios = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="recados_recebidos", verbose_name="destinatários"
    )
    importante = models.BooleanField(default=False, help_text="Destaca o recado no topo do início.")
    criado_em = models.DateTimeField(auto_now_add=True)

    objects = RecadoQuerySet.as_manager()

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return self.titulo

    @property
    def is_privado(self):
        return self.tipo == self.Tipo.PRIVADO

    def publico_alvo(self):
        """Usuários que deveriam ler o recado (para o painel de confirmações)."""
        from accounts.models import User

        if self.is_privado:
            return self.destinatarios.all()
        return User.objects.filter(is_active=True).exclude(pk=self.autor_id)


class Leitura(models.Model):
    recado = models.ForeignKey(Recado, on_delete=models.CASCADE, related_name="leituras")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leituras_recados")
    lido_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["recado", "usuario"], name="leitura_unica")]
