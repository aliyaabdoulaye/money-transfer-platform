"""
Modèles des transactions financières
"""
from django.db import models
from core.models import VirtualAccount
import logging

logger = logging.getLogger('transactions')


class Transaction(models.Model):
    """
    Modèle représentant une transaction financière.
    Toute opération impactant un solde doit être tracée par une transaction.
    """
    
    # Types de transactions
    DEPOSIT = 'deposit'
    TRANSFER = 'transfer'
    WITHDRAWAL = 'withdrawal'
    FEE = 'fee'
    
    TRANSACTION_TYPES = [
        (DEPOSIT, 'Dépôt'),
        (TRANSFER, 'Transfert'),
        (WITHDRAWAL, 'Retrait'),
        (FEE, 'Commission'),
    ]
    
    # Statuts de transaction
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    
    TRANSACTION_STATUS = [
        (PENDING, 'En attente'),
        (COMPLETED, 'Complétée'),
        (FAILED, 'Échouée'),
    ]
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name="Type de transaction"
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Montant",
        help_text="Montant de la transaction en FCFA"
    )
    
    sender_account = models.ForeignKey(
        VirtualAccount,
        on_delete=models.PROTECT,
        related_name='sent_transactions',
        verbose_name="Compte émetteur"
    )
    
    receiver_account = models.ForeignKey(
        VirtualAccount,
        on_delete=models.PROTECT,
        related_name='received_transactions',
        null=True,
        blank=True,
        verbose_name="Compte destinataire",
        help_text="NULL pour les retraits"
    )
    
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS,
        default=COMPLETED,
        verbose_name="Statut"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    
    reference = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Référence",
        help_text="Référence unique de la transaction"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['sender_account', '-created_at']),
            models.Index(fields=['receiver_account', '-created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        receiver_info = f" → {self.receiver_account.user.username}" if self.receiver_account else " → Retrait"
        return f"{self.get_transaction_type_display()} de {self.amount} FCFA - {self.sender_account.user.username}{receiver_info}"
    
    def save(self, *args, **kwargs):
        """Override save pour logger toutes les transactions"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            sender_name = self.sender_account.user.username
            receiver_name = self.receiver_account.user.username if self.receiver_account else "Retrait"
            logger.info(
                f"Transaction créée: {self.get_transaction_type_display()} | "
                f"Montant: {self.amount} FCFA | "
                f"De: {sender_name} | "
                f"Vers: {receiver_name} | "
                f"Ref: {self.reference}"
            )
    
    @classmethod
    def calculate_total_fees(cls):
        """Calcule le total des commissions perçues par la plateforme"""
        total = cls.objects.filter(
            transaction_type=cls.FEE,
            status=cls.COMPLETED
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0
        return total
    
    @classmethod
    def get_transaction_volume(cls):
        """Retourne le volume total des transactions"""
        return cls.objects.filter(status=cls.COMPLETED).count()
    
    @classmethod
    def get_total_amount_transacted(cls):
        """Retourne le montant total transacté (hors fees)"""
        total = cls.objects.filter(
            status=cls.COMPLETED
        ).exclude(
            transaction_type=cls.FEE
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0
        return total