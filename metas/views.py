from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.permissions import proprietario_required
from core.utils import inicio_do_mes, mes_anterior, parse_mes, proximo_mes

from .forms import LancamentoForm, MetaForm
from .models import Lancamento, MetaMensal


def _url_mes(mes):
    return f"{reverse('metas:lista')}?mes={mes:%Y-%m}"


@login_required
def lista(request):
    mes = parse_mes(request.GET.get("mes")) if request.GET.get("mes") else inicio_do_mes()
    metas = (
        MetaMensal.objects.visiveis_para(request.user)
        .do_mes(mes)
        .com_progresso()
        .select_related("responsavel")
    )
    da_farmacia = [m for m in metas if not m.is_individual]
    individuais = [m for m in metas if m.is_individual]

    # Proprietário vê as metas individuais agrupadas por colaborador
    por_colaborador = OrderedDict()
    if request.user.is_proprietario:
        for meta in sorted(individuais, key=lambda m: m.responsavel.nome_exibicao):
            por_colaborador.setdefault(meta.responsavel, []).append(meta)

    contexto = {
        "mes": mes,
        "mes_anterior": mes_anterior(mes),
        "proximo_mes": proximo_mes(mes),
        "mes_atual": inicio_do_mes(),
        "da_farmacia": da_farmacia,
        "individuais": individuais,
        "por_colaborador": por_colaborador,
    }
    return render(request, "metas/lista.html", contexto)


@login_required
def detalhe(request, pk):
    meta = get_object_or_404(
        MetaMensal.objects.visiveis_para(request.user).com_progresso().select_related("responsavel"), pk=pk
    )
    pode_lancar = meta.pode_lancar(request.user)
    form = LancamentoForm(request.POST or None) if pode_lancar else None
    if request.method == "POST":
        if not pode_lancar:
            raise PermissionDenied
        if form.is_valid():
            lancamento = form.save(commit=False)
            lancamento.meta = meta
            lancamento.lancado_por = request.user
            lancamento.save()
            messages.success(request, "Progresso lançado.")
            return redirect("metas:detalhe", pk=pk)
    lancamentos = meta.lancamentos.select_related("lancado_por")
    return render(
        request,
        "metas/detalhe.html",
        {"meta": meta, "form": form, "lancamentos": lancamentos, "pode_lancar": pode_lancar},
    )


@require_POST
@login_required
def apagar_lancamento(request, pk):
    lancamento = get_object_or_404(Lancamento.objects.select_related("meta"), pk=pk)
    meta = lancamento.meta
    if not MetaMensal.objects.visiveis_para(request.user).filter(pk=meta.pk).exists():
        raise PermissionDenied
    if not (request.user.is_proprietario or (lancamento.lancado_por_id == request.user.pk and meta.pode_lancar(request.user))):
        raise PermissionDenied
    lancamento.delete()
    messages.success(request, "Lançamento removido.")
    return redirect("metas:detalhe", pk=meta.pk)


@proprietario_required
def nova(request):
    inicial = {"mes": parse_mes(request.GET["mes"]) if request.GET.get("mes") else inicio_do_mes()}
    if request.GET.get("responsavel", "").isdigit():
        inicial["responsavel"] = request.GET["responsavel"]
        inicial["escopo"] = MetaMensal.Escopo.INDIVIDUAL
    form = MetaForm(request.POST or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        meta = form.save(commit=False)
        meta.criada_por = request.user
        meta.save()
        messages.success(request, "Meta criada.")
        return redirect(_url_mes(meta.mes))
    return render(request, "metas/form.html", {"form": form, "titulo": "Nova meta"})


@proprietario_required
def editar(request, pk):
    meta = get_object_or_404(MetaMensal, pk=pk)
    form = MetaForm(request.POST or None, instance=meta)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Meta atualizada.")
        return redirect("metas:detalhe", pk=pk)
    return render(request, "metas/form.html", {"form": form, "titulo": "Editar meta", "meta": meta})


@require_POST
@proprietario_required
def apagar(request, pk):
    meta = get_object_or_404(MetaMensal, pk=pk)
    mes = meta.mes
    meta.delete()
    messages.success(request, "Meta apagada.")
    return redirect(_url_mes(mes))


@require_POST
@proprietario_required
def copiar_mes_anterior(request):
    """Copia as metas do mês anterior (sem os lançamentos) para o mês indicado."""
    mes = parse_mes(request.POST.get("mes"))
    origem = MetaMensal.objects.do_mes(mes_anterior(mes))
    existentes = set(
        MetaMensal.objects.do_mes(mes).values_list("titulo", "escopo", "responsavel_id")
    )
    novas = [
        MetaMensal(
            titulo=m.titulo,
            descricao=m.descricao,
            mes=mes,
            escopo=m.escopo,
            responsavel=m.responsavel,
            valor_alvo=m.valor_alvo,
            unidade=m.unidade,
            criada_por=request.user,
        )
        for m in origem.select_related("responsavel")
        if (m.titulo, m.escopo, m.responsavel_id) not in existentes
        and (m.responsavel is None or m.responsavel.is_active)
    ]
    MetaMensal.objects.bulk_create(novas)
    if novas:
        messages.success(request, f"{len(novas)} meta(s) copiada(s) do mês anterior.")
    else:
        messages.info(request, "Nenhuma meta nova para copiar do mês anterior.")
    return redirect(_url_mes(mes))
