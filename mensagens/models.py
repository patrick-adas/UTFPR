from django.conf import settings
from django.db import models
from django.db.models import Count


class ConversaQuerySet(models.QuerySet):
    def do_usuario(self, user):
        return self.filter(participantes=user)

    def entre(self, a, b):
        """Conversa 1:1 entre dois usuários (ou None)."""
        # A contagem precisa vir ANTES dos filtros por participante; caso contrário
        # ela conta só as linhas do JOIN filtrado.
        return (
            self.annotate(n=Count("participantes", distinct=True))
            .filter(n=2)
            .filter(participantes=a)
            .filter(participantes=b)
            .order_by("pk")
            .first()
        )


class Conversa(models.Model):
    participantes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="conversas")
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = ConversaQuerySet.as_manager()

    class Meta:
        ordering = ["-atualizada_em"]

    def __str__(self):
        return " ↔ ".join(str(p) for p in self.participantes.all())

    @classmethod
    def obter_ou_criar(cls, a, b):
        conversa = cls.objects.entre(a, b)
        if conversa is None:
            conversa = cls.objects.create()
            conversa.participantes.add(a, b)
        return conversa

    def outro_participante(self, user):
        for p in self.participantes.all():
            if p.pk != user.pk:
                return p
        return user

    def nao_lidas_para(self, user):
        leitura = self.leituras.filter(usuario=user).first()
        qs = self.mensagens.exclude(autor=user)
        if leitura:
            qs = qs.filter(pk__gt=leitura.ultima_mensagem_id or 0)
        return qs.count()

    def marcar_lida(self, user):
        ultima = self.mensagens.order_by("-pk").values_list("pk", flat=True).first()
        LeituraConversa.objects.update_or_create(
            conversa=self, usuario=user, defaults={"ultima_mensagem_id": ultima or 0}
        )


class Mensagem(models.Model):
    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name="mensagens")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mensagens")
    texto = models.TextField(max_length=2000)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["pk"]
        verbose_name_plural = "mensagens"

    def __str__(self):
        return f"{self.autor}: {self.texto[:40]}"

    def save(self, *args, **kwargs):
        novo = self._state.adding
        super().save(*args, **kwargs)
        if novo:
            Conversa.objects.filter(pk=self.conversa_id).update(atualizada_em=self.criada_em)


class LeituraConversa(models.Model):
    """Guarda a última mensagem lida por cada participante (para contar não lidas)."""

    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name="leituras")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ultima_mensagem_id = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["conversa", "usuario"], name="leitura_conversa_unica")]


def total_nao_lidas(user):
    return sum(c.nao_lidas_para(user) for c in Conversa.objects.do_usuario(user).prefetch_related("leituras"))
