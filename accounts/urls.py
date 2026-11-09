from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "entrar/",
        auth_views.LoginView.as_view(template_name="accounts/login.html", redirect_authenticated_user=True),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("senha/", views.trocar_senha, name="trocar_senha"),
    path("perfil/", views.perfil, name="perfil"),
    path("equipe/", views.equipe, name="equipe"),
    path("equipe/novo/", views.colaborador_novo, name="colaborador_novo"),
    path("equipe/<int:pk>/", views.colaborador_editar, name="colaborador_editar"),
    path("equipe/<int:pk>/ativo/", views.colaborador_ativo, name="colaborador_ativo"),
    path("equipe/<int:pk>/senha/", views.colaborador_redefinir_senha, name="colaborador_redefinir_senha"),
]
