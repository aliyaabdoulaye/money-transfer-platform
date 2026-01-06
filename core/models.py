"""
Modèles du core de l'application
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle User.
    Gère la création d'utilisateurs avec phone_number obligatoire.
    """
    
    def _create_user(self, username, email, phone_number, password, **extra_fields):
        """
        Crée et sauvegarde un utilisateur avec les informations données.
        """
        if not username:
            raise ValueError('Le nom d\'utilisateur est obligatoire')
        if not email:
            raise ValueError('L\'email est obligatoire')
        if not phone_number:
            raise ValueError('Le numéro de téléphone est obligatoire')
        
        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, username, email, phone_number, password=None, **extra_fields):
        """
        Crée un utilisateur normal.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False)
        return self._create_user(username, email, phone_number, password, **extra_fields)
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Crée un superutilisateur.
        Pour les superusers, phone_number est optionnel (valeur par défaut).
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) 
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Les superusers doivent avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Les superusers doivent avoir is_superuser=True.')
        
        # Pour les superusers, si phone_number n'est pas fourni, utiliser un numéro basé sur l'username
        phone_number = extra_fields.pop('phone_number', None)
        if not phone_number:
            # Générer un numéro unique basé sur l'username
            phone_number = f"+228{hash(username) % 100000000:08d}"
        
        return self._create_user(username, email, phone_number, password, **extra_fields)


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
    
    # Utiliser le manager personnalisé
    objects = UserManager()
    
    # Champs requis pour la création d'utilisateur
    REQUIRED_FIELDS = ['email', 'phone_number']
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.phone_number})"
    
    def save(self, *args, **kwargs):
        """Override save pour logger la création d'utilisateur"""
        is_new = self.pk is None
        
        # Activer automatiquement les superusers
        if self.is_superuser and not self.is_active:
            self.is_active = True
        
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