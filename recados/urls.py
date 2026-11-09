from django.urls import path

from . import views

app_name = "recados"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("novo/", views.novo, name="novo"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/lido/", views.marcar_lido, name="marcar_lido"),
    path("<int:pk>/apagar/", views.apagar, name="apagar"),
]
