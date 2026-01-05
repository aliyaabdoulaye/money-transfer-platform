"""
Configuration de l'interface d'administration pour l'app transactions
"""
from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Configuration de l'admin pour le modèle Transaction"""
    
    list_display = [
        'reference', 
        'transaction_type', 
        'amount', 
        'sender_account', 
        'receiver_account', 
        'status',
        'created_at'
    ]
    
    list_filter = ['transaction_type', 'status', 'created_at']
    
    search_fields = [
        'reference',
        'sender_account__user__username',
        'receiver_account__user__username',
        'description'
    ]
    
    readonly_fields = [
        'reference',
        'transaction_type',
        'amount',
        'sender_account',
        'receiver_account',
        'status',
        'description',
        'created_at'
    ]
    
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations de la transaction', {
            'fields': ('reference', 'transaction_type', 'amount', 'status')
        }),
        ('Comptes', {
            'fields': ('sender_account', 'receiver_account')
        }),
        ('Détails', {
            'fields': ('description', 'created_at')
        }),
    )
    
    def has_add_permission(self, request):
        """Empêche la création manuelle de transactions"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression de transactions"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Empêche la modification de transactions"""
        return False