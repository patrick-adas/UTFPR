from django.urls import path

from . import views

app_name = "mensagens"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("com/<int:user_id>/", views.iniciar, name="iniciar"),
    path("<int:pk>/", views.conversa, name="conversa"),
    path("<int:pk>/novas/", views.novas, name="novas"),
    path("<int:pk>/enviar/", views.enviar, name="enviar"),
]
