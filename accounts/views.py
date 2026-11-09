from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import proprietario_required

from .forms import ColaboradorForm, PerfilForm, RedefinirSenhaForm
from .models import User


@login_required
def trocar_senha(request):
    obrigatoria = request.user.deve_trocar_senha
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.deve_trocar_senha = False
        user.save(update_fields=["deve_trocar_senha"])
        update_session_auth_hash(request, user)
        messages.success(request, "Senha alterada com sucesso.")
        return redirect("core:inicio")
    return render(request, "accounts/trocar_senha.html", {"form": form, "obrigatoria": obrigatoria})


@login_required
def perfil(request):
    form = PerfilForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Perfil atualizado.")
        return redirect("accounts:perfil")
    return render(request, "accounts/perfil.html", {"form": form})


@proprietario_required
def equipe(request):
    usuarios = User.objects.order_by("-is_active", "papel", "first_name")
    return render(request, "accounts/equipe.html", {"usuarios": usuarios})


@proprietario_required
def colaborador_novo(request):
    form = ColaboradorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"Conta de {user.nome_exibicao} criada. Login: {user.username}")
        return redirect("accounts:equipe")
    return render(request, "accounts/colaborador_form.html", {"form": form, "titulo": "Novo colaborador"})


@proprietario_required
def colaborador_editar(request, pk):
    colaborador = get_object_or_404(User, pk=pk)
    form = ColaboradorForm(request.POST or None, instance=colaborador)
    if request.method == "POST" and form.is_valid():
        if colaborador == request.user and form.cleaned_data["papel"] != User.Papel.PROPRIETARIO:
            form.add_error("papel", "Você não pode remover o seu próprio papel de proprietário.")
        else:
            form.save()
            messages.success(request, "Dados atualizados.")
            return redirect("accounts:equipe")
    senha_form = RedefinirSenhaForm()
    return render(
        request,
        "accounts/colaborador_form.html",
        {"form": form, "titulo": f"Editar {colaborador.nome_exibicao}", "colaborador": colaborador, "senha_form": senha_form},
    )


@require_POST
@proprietario_required
def colaborador_ativo(request, pk):
    colaborador = get_object_or_404(User, pk=pk)
    if colaborador == request.user:
        messages.error(request, "Você não pode desativar a sua própria conta.")
    else:
        colaborador.is_active = not colaborador.is_active
        colaborador.save(update_fields=["is_active"])
        estado = "reativada" if colaborador.is_active else "desativada"
        messages.success(request, f"Conta de {colaborador.nome_exibicao} {estado}.")
    return redirect("accounts:equipe")


@require_POST
@proprietario_required
def colaborador_redefinir_senha(request, pk):
    colaborador = get_object_or_404(User, pk=pk)
    form = RedefinirSenhaForm(request.POST)
    if form.is_valid():
        colaborador.set_password(form.cleaned_data["nova_senha"])
        colaborador.deve_trocar_senha = True
        colaborador.save()
        messages.success(request, f"Senha de {colaborador.nome_exibicao} redefinida. Ele(a) deverá trocá-la no próximo acesso.")
    else:
        messages.error(request, " ".join(form.errors.get("nova_senha", ["Senha inválida."])))
    return redirect("accounts:colaborador_editar", pk=pk)
