"""
Configuration de l'interface d'administration pour l'app core
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, VirtualAccount


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Configuration de l'admin pour le modèle User"""
    
    list_display = ['username', 'email', 'phone_number', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['username', 'email', 'phone_number', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('phone_number', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('phone_number', 'email')
        }),
    )


@admin.register(VirtualAccount)
class VirtualAccountAdmin(admin.ModelAdmin):
    """Configuration de l'admin pour le modèle VirtualAccount"""
    
    list_display = ['user', 'balance', 'is_suspended', 'is_platform_account', 'created_at']
    list_filter = ['is_suspended', 'is_platform_account', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__phone_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations du compte', {
            'fields': ('user', 'balance', 'is_platform_account')
        }),
        ('Statut', {
            'fields': ('is_suspended',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression du compte plateforme"""
        if obj and obj.is_platform_account:
            return False
        return super().has_delete_permission(request, obj)