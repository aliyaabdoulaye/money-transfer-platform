"""
Modèles du core de l'application
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé.
    Étend le modèle User par défaut de Django.
    """
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro de téléphone doit être au format: '+999999999'. Maximum 15 chiffres."
    )
    
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        unique=True,
        verbose_name="Numéro de téléphone"
    )
    
    is_active = models.BooleanField(
        default=False,
        verbose_name="Compte activé",
        help_text="Le compte doit être activé avec un OTP après l'inscription"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.phone_number})"
    
    def save(self, *args, **kwargs):
        """Override save pour logger la création d'utilisateur"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"Nouvel utilisateur créé: {self.username} - {self.phone_number}")


class VirtualAccount(models.Model):
    """
    Compte virtuel associé à chaque utilisateur.
    Représente le solde électronique de l'utilisateur.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='virtual_account',
        verbose_name="Utilisateur"
    )
    
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Solde",
        help_text="Solde actuel du compte virtuel"
    )
    
    is_suspended = models.BooleanField(
        default=False,
        verbose_name="Compte suspendu",
        help_text="Un compte suspendu ne peut effectuer aucune opération"
    )
    
    is_platform_account = models.BooleanField(
        default=False,
        verbose_name="Compte plateforme",
        help_text="Indique si c'est le compte de la plateforme"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Compte virtuel"
        verbose_name_plural = "Comptes virtuels"
        ordering = ['-created_at']
    
    def __str__(self):
        status = "SUSPENDU" if self.is_suspended else "ACTIF"
        platform_tag = " [PLATEFORME]" if self.is_platform_account else ""
        return f"Compte de {self.user.username} - {self.balance} FCFA ({status}){platform_tag}"
    
    def can_perform_operations(self):
        """Vérifie si le compte peut effectuer des opérations"""
        return not self.is_suspended and self.user.is_active
    
    def suspend(self):
        """Suspend le compte virtuel"""
        if not self.is_platform_account:
            self.is_suspended = True
            self.save()
            logger.warning(f"Compte suspendu: {self.user.username}")
    
    def reactivate(self):
        """Réactive le compte virtuel"""
        self.is_suspended = False
        self.save()
        logger.info(f"Compte réactivé: {self.user.username}")
    
    def save(self, *args, **kwargs):
        """Override save pour logger les changements de suspension"""
        if self.pk:
            old_instance = VirtualAccount.objects.get(pk=self.pk)
            if old_instance.is_suspended != self.is_suspended:
                if self.is_suspended:
                    logger.warning(f"Suspension du compte: {self.user.username}")
                else:
                    logger.info(f"Réactivation du compte: {self.user.username}")
        super().save(*args, **kwargs)