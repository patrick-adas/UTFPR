from django.urls import path

from . import views

app_name = "metas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nova/", views.nova, name="nova"),
    path("copiar-mes-anterior/", views.copiar_mes_anterior, name="copiar_mes_anterior"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/apagar/", views.apagar, name="apagar"),
    path("lancamento/<int:pk>/apagar/", views.apagar_lancamento, name="apagar_lancamento"),
]
