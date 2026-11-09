from django.conf import settings
from django.db import models


class Post(models.Model):
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    texto = models.TextField(max_length=3000)
    imagem = models.ImageField(upload_to="feed/", blank=True)
    fixado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fixado", "-criado_em"]

    def __str__(self):
        return f"{self.autor}: {self.texto[:40]}"

    def pode_apagar(self, user):
        return user == self.autor or user.is_proprietario


class Comentario(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comentarios")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comentarios")
    texto = models.TextField(max_length=1000)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["criado_em"]
        verbose_name = "comentário"

    def __str__(self):
        return f"{self.autor}: {self.texto[:40]}"

    def pode_apagar(self, user):
        return user == self.autor or user.is_proprietario


class Curtida(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="curtidas")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="curtidas")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["post", "usuario"], name="curtida_unica")]
