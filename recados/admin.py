from django.contrib import admin

from .models import Leitura, Recado


@admin.register(Recado)
class RecadoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "tipo", "importante", "criado_em")
    list_filter = ("tipo", "importante")
    filter_horizontal = ("destinatarios",)


admin.site.register(Leitura)
