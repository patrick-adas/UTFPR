from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from accounts.models import User

from .models import Conversa, Mensagem

LIMITE_HISTORICO = 200


def _conversa_do_usuario(request, pk):
    return get_object_or_404(Conversa.objects.do_usuario(request.user).prefetch_related("participantes"), pk=pk)


@login_required
def lista(request):
    conversas = Conversa.objects.do_usuario(request.user).prefetch_related("participantes")
    itens = []
    for conversa in conversas:
        ultima = conversa.mensagens.select_related("autor").order_by("-pk").first()
        if ultima is None:
            continue
        itens.append(
            {
                "conversa": conversa,
                "outro": conversa.outro_participante(request.user),
                "ultima": ultima,
                "nao_lidas": conversa.nao_lidas_para(request.user),
            }
        )
    colegas = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
    return render(request, "mensagens/lista.html", {"itens": itens, "colegas": colegas})


@login_required
def iniciar(request, user_id):
    outro = get_object_or_404(User, pk=user_id, is_active=True)
    if outro == request.user:
        raise Http404
    conversa = Conversa.obter_ou_criar(request.user, outro)
    return redirect("mensagens:conversa", pk=conversa.pk)


@login_required
def conversa(request, pk):
    conversa = _conversa_do_usuario(request, pk)
    mensagens = list(conversa.mensagens.select_related("autor").order_by("-pk")[:LIMITE_HISTORICO])[::-1]
    conversa.marcar_lida(request.user)
    return render(
        request,
        "mensagens/conversa.html",
        {
            "conversa": conversa,
            "outro": conversa.outro_participante(request.user),
            "mensagens": mensagens,
            "ultimo_id": mensagens[-1].pk if mensagens else 0,
            "intervalo": settings.POLLING_CHAT_SEGUNDOS,
        },
    )


@require_GET
@login_required
def novas(request, pk):
    """Endpoint de polling: devolve só as mensagens com id maior que `depois`."""
    conversa = _conversa_do_usuario(request, pk)
    try:
        depois = int(request.GET.get("depois", 0))
    except ValueError:
        depois = 0
    mensagens = list(conversa.mensagens.select_related("autor").filter(pk__gt=depois))
    if mensagens:
        conversa.marcar_lida(request.user)
    return render(
        request,
        "mensagens/_novas.html",
        {
            "conversa": conversa,
            "mensagens": mensagens,
            "ultimo_id": mensagens[-1].pk if mensagens else depois,
            "intervalo": settings.POLLING_CHAT_SEGUNDOS,
        },
    )


@require_POST
@login_required
def enviar(request, pk):
    conversa = _conversa_do_usuario(request, pk)
    texto = request.POST.get("texto", "").strip()[:2000]
    if texto:
        Mensagem.objects.create(conversa=conversa, autor=request.user, texto=texto)
    if request.htmx:
        # O poller da conversa escuta este evento e busca as novas mensagens na hora.
        return HttpResponse(status=204, headers={"HX-Trigger": "mensagemEnviada"})
    return redirect("mensagens:conversa", pk=pk)
