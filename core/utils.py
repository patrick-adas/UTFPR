import datetime

from django.shortcuts import redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme


def redirecionar_next(request, padrao):
    """Redireciona para o campo `next` do POST, se for uma URL local segura."""
    destino = request.POST.get("next") or request.GET.get("next")
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(destino)
    return redirect(padrao)


def inicio_do_mes(data=None):
    data = data or timezone.localdate()
    return data.replace(day=1)


def mes_anterior(mes):
    return (mes - datetime.timedelta(days=1)).replace(day=1)


def proximo_mes(mes):
    return (mes.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)


def parse_mes(texto):
    """Converte 'AAAA-MM' em date no dia 1; devolve o mês atual se inválido."""
    try:
        ano, mes = texto.split("-")
        return datetime.date(int(ano), int(mes), 1)
    except (AttributeError, ValueError):
        return inicio_do_mes()
