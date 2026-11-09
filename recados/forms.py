from django import forms

from accounts.models import User

from .models import Recado


class RecadoForm(forms.ModelForm):
    class Meta:
        model = Recado
        fields = ["titulo", "texto", "tipo", "destinatarios", "importante"]
        widgets = {
            "texto": forms.Textarea(attrs={"rows": 4}),
            "destinatarios": forms.CheckboxSelectMultiple,
            "tipo": forms.RadioSelect,
        }

    def __init__(self, *args, autor=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = User.objects.filter(is_active=True)
        if autor is not None:
            qs = qs.exclude(pk=autor.pk)
        self.fields["destinatarios"].queryset = qs
        self.fields["destinatarios"].help_text = "Usado apenas quando o recado é privado."

    def clean(self):
        dados = super().clean()
        if dados.get("tipo") == Recado.Tipo.PRIVADO and not dados.get("destinatarios"):
            self.add_error("destinatarios", "Escolha ao menos um destinatário para o recado privado.")
        if dados.get("tipo") == Recado.Tipo.GERAL:
            dados["destinatarios"] = User.objects.none()
        return dados
