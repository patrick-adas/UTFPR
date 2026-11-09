import datetime
from decimal import Decimal

from django import template
from django.utils import timezone
from django.utils.html import format_html
from django.utils.timesince import timesince

register = template.Library()


def _numero_br(valor, casas):
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


@register.filter
def numero(valor):
    """Formata número no padrão brasileiro, sem casas decimais se for inteiro."""
    if valor is None:
        return ""
    valor = Decimal(valor)
    casas = 0 if valor == valor.to_integral_value() else 2
    return _numero_br(valor, casas)


@register.filter
def valor_meta(valor, unidade):
    """Ex.: (1500, 'R$') -> 'R$ 1.500,00'; (30, 'atendimentos') -> '30 atendimentos'."""
    if valor is None:
        return ""
    valor = Decimal(valor)
    if unidade and unidade.strip().upper() == "R$":
        return f"R$ {_numero_br(valor, 2)}"
    return f"{numero(valor)} {unidade}".strip()


@register.filter
def percentual(valor):
    """45.0 -> '45'; 47.1 -> '47,1'."""
    if valor is None:
        return "0"
    texto = f"{float(valor):.1f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


@register.filter
def quando(data):
    """Tempo relativo amigável: 'agora', 'há 5 minutos', 'há 2 dias'."""
    if not data:
        return ""
    if timezone.now() - data < datetime.timedelta(minutes=1):
        return "agora"
    return f"há {timesince(data).split(',')[0]}"


@register.simple_tag
def avatar(user, tamanho="md"):
    if user is None:
        return ""
    if user.foto:
        return format_html('<img class="avatar avatar-{}" src="{}" alt="{}">', tamanho, user.foto.url, user.nome_exibicao)
    cor = (user.pk or 0) % 6
    return format_html(
        '<span class="avatar avatar-{} avatar-cor-{}" aria-hidden="true">{}</span>', tamanho, cor, user.iniciais
    )


@register.filter
def cor_progresso(percentual):
    try:
        p = float(percentual)
    except (TypeError, ValueError):
        return "baixo"
    if p >= 100:
        return "atingida"
    if p >= 70:
        return "alto"
    if p >= 40:
        return "medio"
    return "baixo"
