from django.urls import path

from . import views

app_name = "tarefas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nova/", views.nova, name="nova"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/status/", views.mudar_status, name="mudar_status"),
    path("<int:pk>/apagar/", views.apagar, name="apagar"),
]
