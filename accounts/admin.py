from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "get_full_name", "papel", "cargo", "is_active")
    list_filter = ("papel", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Farmácia", {"fields": ("papel", "cargo", "telefone", "foto", "deve_trocar_senha")}),
    )
