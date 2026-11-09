from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import proprietario_required

from .forms import ComentarioForm, PostForm
from .models import Comentario, Curtida, Post


def posts_com_anotacoes(user):
    """Queryset do feed com contagens e flag 'curtido' pelo usuário atual."""
    return (
        Post.objects.select_related("autor")
        .prefetch_related(Prefetch("comentarios", queryset=Comentario.objects.select_related("autor")))
        .annotate(
            total_curtidas=Count("curtidas", distinct=True),
            curtido=Exists(Curtida.objects.filter(post=OuterRef("pk"), usuario=user)),
        )
        .order_by("-fixado", "-criado_em")
    )


def _render_post(request, post_id):
    post = posts_com_anotacoes(request.user).get(pk=post_id)
    return render(request, "feed/_post.html", {"post": post, "comentario_form": ComentarioForm()})


@require_POST
@login_required
def postar(request):
    form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.autor = request.user
        post.save()
        messages.success(request, "Recado publicado no feed.")
    else:
        messages.error(request, "Não foi possível publicar: escreva algum texto.")
    return redirect("core:inicio")


@require_POST
@login_required
def comentar(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = ComentarioForm(request.POST)
    if form.is_valid():
        Comentario.objects.create(post=post, autor=request.user, texto=form.cleaned_data["texto"])
    if request.htmx:
        return _render_post(request, post.pk)
    return redirect(f"/#post-{post.pk}")


@require_POST
@login_required
def curtir(request, pk):
    post = get_object_or_404(Post, pk=pk)
    curtida, criada = Curtida.objects.get_or_create(post=post, usuario=request.user)
    if not criada:
        curtida.delete()
    if request.htmx:
        return _render_post(request, post.pk)
    return redirect(f"/#post-{post.pk}")


@require_POST
@proprietario_required
def fixar(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.fixado = not post.fixado
    post.save(update_fields=["fixado"])
    messages.success(request, "Post fixado no topo." if post.fixado else "Post desafixado.")
    return redirect("core:inicio")


@require_POST
@login_required
def apagar(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not post.pode_apagar(request.user):
        raise PermissionDenied
    post.delete()
    messages.success(request, "Post apagado.")
    return redirect("core:inicio")


@require_POST
@login_required
def apagar_comentario(request, pk):
    comentario = get_object_or_404(Comentario, pk=pk)
    if not comentario.pode_apagar(request.user):
        raise PermissionDenied
    post_id = comentario.post_id
    comentario.delete()
    if request.htmx:
        return _render_post(request, post_id)
    return redirect(f"/#post-{post_id}")
