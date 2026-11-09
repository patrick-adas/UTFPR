from django.urls import path

from . import views

app_name = "feed"

urlpatterns = [
    path("postar/", views.postar, name="postar"),
    path("<int:pk>/comentar/", views.comentar, name="comentar"),
    path("<int:pk>/curtir/", views.curtir, name="curtir"),
    path("<int:pk>/fixar/", views.fixar, name="fixar"),
    path("<int:pk>/apagar/", views.apagar, name="apagar"),
    path("comentario/<int:pk>/apagar/", views.apagar_comentario, name="apagar_comentario"),
]
