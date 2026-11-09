from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import proprietario_required
from core.utils import redirecionar_next

from .forms import RecadoForm
from .models import Leitura, Recado


@login_required
def lista(request):
    filtro = request.GET.get("tipo", "")
    recados = (
        Recado.objects.visiveis_para(request.user)
        .select_related("autor")
        .prefetch_related("destinatarios")
        .annotate(lido=Exists(Leitura.objects.filter(recado=OuterRef("pk"), usuario=request.user)))
    )
    if filtro in Recado.Tipo.values:
        recados = recados.filter(tipo=filtro)
    form = RecadoForm(autor=request.user) if request.user.is_proprietario else None
    return render(request, "recados/lista.html", {"recados": recados, "form": form, "filtro": filtro})


@login_required
def detalhe(request, pk):
    recado = get_object_or_404(Recado.objects.visiveis_para(request.user).select_related("autor"), pk=pk)
    if recado.autor != request.user:
        Leitura.objects.get_or_create(recado=recado, usuario=request.user)
    contexto = {"recado": recado}
    if request.user.is_proprietario:
        leituras = {l.usuario_id: l.lido_em for l in recado.leituras.all()}
        contexto["confirmacoes"] = [(u, leituras.get(u.pk)) for u in recado.publico_alvo()]
    return render(request, "recados/detalhe.html", contexto)


@require_POST
@proprietario_required
def novo(request):
    form = RecadoForm(request.POST, autor=request.user)
    if form.is_valid():
        recado = form.save(commit=False)
        recado.autor = request.user
        recado.save()
        form.save_m2m()
        messages.success(request, "Recado enviado.")
        return redirect("recados:lista")
    recados = Recado.objects.visiveis_para(request.user).select_related("autor")
    return render(request, "recados/lista.html", {"recados": recados, "form": form, "abrir_form": True})


@require_POST
@login_required
def marcar_lido(request, pk):
    recado = get_object_or_404(Recado.objects.visiveis_para(request.user), pk=pk)
    Leitura.objects.get_or_create(recado=recado, usuario=request.user)
    return redirecionar_next(request, "recados:lista")


@require_POST
@proprietario_required
def apagar(request, pk):
    recado = get_object_or_404(Recado, pk=pk)
    if recado.autor != request.user:
        raise Http404
    recado.delete()
    messages.success(request, "Recado apagado.")
    return redirect("recados:lista")
