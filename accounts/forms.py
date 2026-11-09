from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import User


class ColaboradorForm(forms.ModelForm):
    """Criação/edição de colaborador pelo proprietário."""

    senha_inicial = forms.CharField(
        label="Senha inicial",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="O colaborador será obrigado a trocá-la no primeiro acesso.",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "cargo", "telefone", "papel"]
        labels = {
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "username": "Usuário (login)",
            "email": "E-mail",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        if self.instance.pk is None:
            self.fields["senha_inicial"].required = True
        else:
            del self.fields["senha_inicial"]

    def clean_senha_inicial(self):
        senha = self.cleaned_data.get("senha_inicial")
        if senha:
            validate_password(senha)
        return senha

    def save(self, commit=True):
        user = super().save(commit=False)
        senha = self.cleaned_data.get("senha_inicial")
        if senha:
            user.set_password(senha)
            user.deve_trocar_senha = True
        if commit:
            user.save()
        return user


class RedefinirSenhaForm(forms.Form):
    nova_senha = forms.CharField(label="Nova senha temporária", widget=forms.PasswordInput)

    def clean_nova_senha(self):
        senha = self.cleaned_data["nova_senha"]
        validate_password(senha)
        return senha


class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "telefone", "foto"]
        labels = {"first_name": "Nome", "last_name": "Sobrenome", "email": "E-mail"}
