from django import forms
from django.utils import timezone

from accounts.models import User

from .models import Lancamento, MetaMensal


class MetaForm(forms.ModelForm):
    mes = forms.DateField(
        label="Mês",
        input_formats=["%Y-%m"],
        widget=forms.DateInput(attrs={"type": "month"}, format="%Y-%m"),
    )

    class Meta:
        model = MetaMensal
        fields = ["titulo", "descricao", "mes", "escopo", "responsavel", "valor_alvo", "unidade"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 2}),
            "escopo": forms.RadioSelect,
            "unidade": forms.TextInput(attrs={"list": "unidades-sugeridas"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsavel"].queryset = User.objects.filter(is_active=True)
        self.fields["responsavel"].help_text = "Obrigatório para metas individuais."

    def clean(self):
        dados = super().clean()
        escopo = dados.get("escopo")
        if escopo == MetaMensal.Escopo.INDIVIDUAL and not dados.get("responsavel"):
            self.add_error("responsavel", "Escolha o colaborador responsável pela meta individual.")
        if escopo == MetaMensal.Escopo.FARMACIA:
            dados["responsavel"] = None
        if dados.get("mes"):
            dados["mes"] = dados["mes"].replace(day=1)
        valor = dados.get("valor_alvo")
        if valor is not None and valor <= 0:
            self.add_error("valor_alvo", "O valor alvo deve ser maior que zero.")
        return dados

    def save(self, commit=True):
        self.instance.responsavel = self.cleaned_data.get("responsavel")
        return super().save(commit)


class LancamentoForm(forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = ["valor", "data", "observacao"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}
        help_texts = {"valor": "Use valor negativo para corrigir um lançamento."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial.setdefault("data", timezone.localdate())
