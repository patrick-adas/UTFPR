from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce


class MetaQuerySet(models.QuerySet):
    def visiveis_para(self, user):
        if user.is_proprietario:
            return self.all()
        return self.filter(Q(escopo=MetaMensal.Escopo.FARMACIA) | Q(responsavel=user))

    def do_mes(self, mes):
        return self.filter(mes=mes)

    def com_progresso(self):
        return self.annotate(
            total_lancado=Coalesce(
                Sum("lancamentos__valor"),
                Value(Decimal("0")),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )


class MetaMensal(models.Model):
    class Escopo(models.TextChoices):
        FARMACIA = "FARMACIA", "Da farmácia (equipe toda)"
        INDIVIDUAL = "INDIVIDUAL", "Individual"

    titulo = models.CharField("título", max_length=150)
    descricao = models.TextField("descrição", blank=True)
    mes = models.DateField("mês", help_text="Sempre o dia 1 do mês de referência.")
    escopo = models.CharField(max_length=12, choices=Escopo.choices, default=Escopo.FARMACIA)
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="metas",
        verbose_name="responsável",
    )
    valor_alvo = models.DecimalField("valor alvo", max_digits=12, decimal_places=2)
    unidade = models.CharField(max_length=30, default="R$", help_text="Ex.: R$, unidades, atendimentos, clientes")
    criada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="metas_criadas"
    )
    criada_em = models.DateTimeField(auto_now_add=True)

    objects = MetaQuerySet.as_manager()

    class Meta:
        ordering = ["-mes", "escopo", "titulo"]
        verbose_name = "meta"
        verbose_name_plural = "metas"
        constraints = [
            models.CheckConstraint(
                condition=Q(escopo="FARMACIA", responsavel__isnull=True)
                | Q(escopo="INDIVIDUAL", responsavel__isnull=False),
                name="meta_escopo_responsavel_coerente",
            ),
            models.CheckConstraint(condition=Q(valor_alvo__gt=0), name="meta_valor_alvo_positivo"),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.mes:%m/%Y})"

    @property
    def is_individual(self):
        return self.escopo == self.Escopo.INDIVIDUAL

    @property
    def valor_atual(self):
        total = getattr(self, "total_lancado", None)
        if total is None:
            total = self.lancamentos.aggregate(t=Sum("valor"))["t"] or Decimal("0")
        return total

    @property
    def percentual(self):
        if not self.valor_alvo:
            return 0
        return round(float(self.valor_atual / self.valor_alvo * 100), 1)

    @property
    def percentual_barra(self):
        """Percentual limitado a 100 para a largura da barra de progresso."""
        return min(self.percentual, 100)

    @property
    def faltante(self):
        return max(self.valor_alvo - self.valor_atual, Decimal("0"))

    @property
    def atingida(self):
        return self.valor_atual >= self.valor_alvo

    def pode_lancar(self, user):
        if user.is_proprietario:
            return True
        return settings.COLABORADOR_PODE_LANCAR and self.is_individual and self.responsavel_id == user.pk


class Lancamento(models.Model):
    meta = models.ForeignKey(MetaMensal, on_delete=models.CASCADE, related_name="lancamentos")
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    observacao = models.CharField("observação", max_length=200, blank=True)
    data = models.DateField()
    lancado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-criado_em"]
        verbose_name = "lançamento"

    def __str__(self):
        return f"{self.meta.titulo}: {self.valor}"
