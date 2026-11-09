from django.conf import settings
from django.db import models
from django.utils import timezone


class TarefaQuerySet(models.QuerySet):
    def visiveis_para(self, user):
        if user.is_proprietario:
            return self.all()
        return self.filter(responsavel=user)

    def abertas(self):
        return self.exclude(status=Tarefa.Status.CONCLUIDA)


class Tarefa(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        CONCLUIDA = "CONCLUIDA", "Concluída"

    class Prioridade(models.IntegerChoices):
        BAIXA = 1, "Baixa"
        MEDIA = 2, "Média"
        ALTA = 3, "Alta"

    titulo = models.CharField("título", max_length=150)
    descricao = models.TextField("descrição", blank=True)
    criada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="tarefas_criadas"
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tarefas", verbose_name="responsável"
    )
    prazo = models.DateField(null=True, blank=True)
    prioridade = models.IntegerField(choices=Prioridade.choices, default=Prioridade.MEDIA)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDENTE)
    criada_em = models.DateTimeField(auto_now_add=True)
    concluida_em = models.DateTimeField(null=True, blank=True)

    objects = TarefaQuerySet.as_manager()

    class Meta:
        ordering = ["status", "prazo", "-prioridade", "-criada_em"]

    def __str__(self):
        return self.titulo

    @property
    def atrasada(self):
        return (
            self.prazo is not None
            and self.status != self.Status.CONCLUIDA
            and self.prazo < timezone.localdate()
        )

    def mudar_status(self, novo_status):
        self.status = novo_status
        self.concluida_em = timezone.now() if novo_status == self.Status.CONCLUIDA else None
        self.save(update_fields=["status", "concluida_em"])


class ComentarioTarefa(models.Model):
    tarefa = models.ForeignKey(Tarefa, on_delete=models.CASCADE, related_name="comentarios")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    texto = models.TextField(max_length=1000)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["criado_em"]
        verbose_name = "comentário da tarefa"
