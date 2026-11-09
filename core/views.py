from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousFileOperation
from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef
from django.http import FileResponse, Http404, HttpResponse
from django.utils._os import safe_join
from django.shortcuts import render
from django.templatetags.static import static
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from feed.forms import ComentarioForm, PostForm
from feed.views import posts_com_anotacoes
from metas.models import MetaMensal
from recados.models import Leitura, Recado
from tarefas.models import Tarefa

from .context_processors import calcular_contadores
from .utils import inicio_do_mes


@login_required
def inicio(request):
    user = request.user
    mes = inicio_do_mes()

    paginador = Paginator(posts_com_anotacoes(user), 15)
    pagina = paginador.get_page(request.GET.get("pagina"))

    recados_destaque = (
        Recado.objects.visiveis_para(user)
        .select_related("autor")
        .annotate(lido=Exists(Leitura.objects.filter(recado=OuterRef("pk"), usuario=user)))
        .filter(importante=True)[:3]
    )
    recados_privados_novos = (
        Recado.objects.nao_lidos_por(user).filter(tipo=Recado.Tipo.PRIVADO).select_related("autor")[:5]
    )

    metas_mes = MetaMensal.objects.do_mes(mes).com_progresso().select_related("responsavel")
    metas_farmacia = metas_mes.filter(escopo=MetaMensal.Escopo.FARMACIA)
    minhas_metas = metas_mes.filter(responsavel=user)

    minhas_tarefas = Tarefa.objects.filter(responsavel=user).abertas().order_by("prazo", "-prioridade")[:6]

    contexto = {
        "pagina": pagina,
        "post_form": PostForm(),
        "comentario_form": ComentarioForm(),
        "recados_destaque": recados_destaque,
        "recados_privados_novos": recados_privados_novos,
        "metas_farmacia": metas_farmacia,
        "minhas_metas": minhas_metas,
        "minhas_tarefas": minhas_tarefas,
        "mes": mes,
    }
    if user.is_proprietario:
        abertas = Tarefa.objects.abertas()
        contexto["resumo_equipe"] = {
            "tarefas_abertas": abertas.count(),
            "tarefas_atrasadas": sum(1 for t in abertas.only("prazo", "status") if t.atrasada),
            "metas_individuais": metas_mes.filter(escopo=MetaMensal.Escopo.INDIVIDUAL).count(),
        }
    return render(request, "core/inicio.html", contexto)


@require_GET
@login_required
def contadores(request):
    """Polling dos badges de não lidos (troca out-of-band no HTMX)."""
    return render(request, "core/_contadores.html", {"contadores": calcular_contadores(request.user)})


@require_GET
@cache_control(max_age=3600)
def manifest(request):
    return render(
        request,
        "core/manifest.webmanifest",
        {"icone_192": static("icons/icon-192.png"), "icone_512": static("icons/icon-512.png"),
         "icone_maskable": static("icons/icon-maskable-512.png")},
        content_type="application/manifest+json",
    )


@require_GET
@cache_control(max_age=0, no_cache=True)
def service_worker(request):
    resposta = render(
        request,
        "core/sw.js",
        {
            "estaticos": [
                static("css/app.css"),
                static("js/app.js"),
                static("js/htmx.min.js"),
                static("icons/icon-192.png"),
            ]
        },
        content_type="application/javascript",
    )
    resposta["Service-Worker-Allowed"] = "/"
    return resposta


@require_GET
def offline(request):
    return render(request, "core/offline.html")


@require_GET
@login_required
def media_protegida(request, caminho):
    """Serve arquivos enviados (fotos) apenas para usuários autenticados."""
    try:
        arquivo = Path(safe_join(settings.MEDIA_ROOT, caminho))
    except SuspiciousFileOperation:
        raise Http404
    if not arquivo.is_file():
        raise Http404
    resposta = FileResponse(arquivo.open("rb"))
    resposta["Cache-Control"] = "private, max-age=86400"
    return resposta


def healthz(request):
    return HttpResponse("ok", content_type="text/plain")
