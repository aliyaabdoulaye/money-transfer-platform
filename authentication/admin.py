"""
Configuration de l'interface d'administration pour l'app authentication
"""
from django.contrib import admin
from .models import OTPCode


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    """Configuration de l'admin pour le modèle OTPCode"""
    
    list_display = [
        'user',
        'code',
        'otp_type',
        'is_used',
        'is_valid_display',
        'expires_at',
        'created_at'
    ]
    
    list_filter = ['otp_type', 'is_used', 'created_at']
    
    search_fields = ['user__username', 'user__email', 'code']
    
    readonly_fields = [
        'user',
        'code',
        'otp_type',
        'is_used',
        'expires_at',
        'created_at',
        'is_valid_display'
    ]
    
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations OTP', {
            'fields': ('user', 'code', 'otp_type')
        }),
        ('Statut', {
            'fields': ('is_used', 'is_valid_display')
        }),
        ('Dates', {
            'fields': ('expires_at', 'created_at')
        }),
    )
    
    def is_valid_display(self, obj):
        """Affiche si l'OTP est valide"""
        return obj.is_valid()
    
    is_valid_display.boolean = True
    is_valid_display.short_description = 'Valide'
    
    def has_add_permission(self, request):
        """Empêche la création manuelle d'OTP"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Permet la suppression uniquement des OTP expirés ou utilisés"""
        if obj and (obj.is_used or not obj.is_valid()):
            return True
        return False
    
    def has_change_permission(self, request, obj=None):
        """Empêche la modification d'OTP"""
        return False