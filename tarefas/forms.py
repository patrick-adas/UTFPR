from django import forms

from accounts.models import User

from .models import Tarefa


class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ["titulo", "descricao", "responsavel", "prazo", "prioridade", "status"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
            "prazo": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsavel"].queryset = User.objects.filter(is_active=True)


class ComentarioTarefaForm(forms.Form):
    texto = forms.CharField(
        label="", max_length=1000, widget=forms.TextInput(attrs={"placeholder": "Atualização ou dúvida sobre a tarefa…"})
    )
