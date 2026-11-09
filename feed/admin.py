from django.contrib import admin

from .models import Comentario, Curtida, Post


class ComentarioInline(admin.TabularInline):
    model = Comentario
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("autor", "texto", "fixado", "criado_em")
    list_filter = ("fixado",)
    inlines = [ComentarioInline]


admin.site.register(Curtida)
