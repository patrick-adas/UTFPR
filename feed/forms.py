from django import forms

from .models import Comentario, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["texto", "imagem"]
        widgets = {
            "texto": forms.Textarea(attrs={"rows": 3, "placeholder": "Deixe um recado para a equipe…"}),
        }
        labels = {"texto": "", "imagem": "Foto (opcional)"}


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ["texto"]
        widgets = {"texto": forms.TextInput(attrs={"placeholder": "Escreva um comentário…", "autocomplete": "off"})}
        labels = {"texto": ""}
