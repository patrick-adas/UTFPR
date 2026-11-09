from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from core.permissions import proprietario_required
from core.utils import redirecionar_next

from .forms import ComentarioTarefaForm, TarefaForm
from .models import ComentarioTarefa, Tarefa


@login_required
def lista(request):
    tarefas = Tarefa.objects.visiveis_para(request.user).select_related("responsavel")
    status = request.GET.get("status", "abertas")
    if status == "abertas":
        tarefas = tarefas.abertas()
    elif status in Tarefa.Status.values:
        tarefas = tarefas.filter(status=status)
    responsavel_id = request.GET.get("responsavel", "")
    if request.user.is_proprietario and responsavel_id.isdigit():
        tarefas = tarefas.filter(responsavel_id=responsavel_id)
    contexto = {
        "tarefas": tarefas,
        "status": status,
        "responsavel_id": responsavel_id,
        "status_opcoes": Tarefa.Status.choices,
        "equipe": User.objects.filter(is_active=True) if request.user.is_proprietario else None,
    }
    return render(request, "tarefas/lista.html", contexto)


@login_required
def detalhe(request, pk):
    tarefa = get_object_or_404(
        Tarefa.objects.visiveis_para(request.user).select_related("responsavel", "criada_por"), pk=pk
    )
    form = ComentarioTarefaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ComentarioTarefa.objects.create(tarefa=tarefa, autor=request.user, texto=form.cleaned_data["texto"])
        return redirect("tarefas:detalhe", pk=pk)
    return render(
        request,
        "tarefas/detalhe.html",
        {"tarefa": tarefa, "form": form, "comentarios": tarefa.comentarios.select_related("autor"), "status_opcoes": Tarefa.Status.choices},
    )


@require_POST
@login_required
def mudar_status(request, pk):
    tarefa = get_object_or_404(Tarefa.objects.visiveis_para(request.user), pk=pk)
    novo = request.POST.get("status")
    if novo in Tarefa.Status.values:
        tarefa.mudar_status(novo)
        messages.success(request, f"“{tarefa.titulo}” marcada como {tarefa.get_status_display().lower()}.")
    return redirecionar_next(request, "tarefas:lista")


@proprietario_required
def nova(request):
    inicial = {}
    if request.GET.get("responsavel", "").isdigit():
        inicial["responsavel"] = request.GET["responsavel"]
    form = TarefaForm(request.POST or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        tarefa = form.save(commit=False)
        tarefa.criada_por = request.user
        tarefa.save()
        messages.success(request, f"Tarefa atribuída a {tarefa.responsavel.nome_exibicao}.")
        return redirect("tarefas:lista")
    return render(request, "tarefas/form.html", {"form": form, "titulo": "Nova tarefa"})


@proprietario_required
def editar(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    form = TarefaForm(request.POST or None, instance=tarefa)
    if request.method == "POST" and form.is_valid():
        tarefa = form.save(commit=False)
        if "status" in form.changed_data:
            concluida = tarefa.status == Tarefa.Status.CONCLUIDA
            tarefa.concluida_em = timezone.now() if concluida else None
        tarefa.save()
        messages.success(request, "Tarefa atualizada.")
        return redirect("tarefas:detalhe", pk=pk)
    return render(request, "tarefas/form.html", {"form": form, "titulo": "Editar tarefa", "tarefa": tarefa})


@require_POST
@proprietario_required
def apagar(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    tarefa.delete()
    messages.success(request, "Tarefa apagada.")
    return redirect("tarefas:lista")
