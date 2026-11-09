from django.contrib import admin
from django.urls import include, path

from core.views import media_protegida

admin.site.site_header = "Rede Farmácia — Administração"
admin.site.site_title = "Rede Farmácia"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("conta/", include("accounts.urls")),
    path("feed/", include("feed.urls")),
    path("recados/", include("recados.urls")),
    path("tarefas/", include("tarefas.urls")),
    path("metas/", include("metas.urls")),
    path("mensagens/", include("mensagens.urls")),
    # Fotos de perfil e imagens do feed: só para usuários logados.
    path("media/<path:caminho>", media_protegida, name="media"),
]
