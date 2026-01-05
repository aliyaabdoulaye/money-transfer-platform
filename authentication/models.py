"""
Modèles d'authentification et OTP
"""
from django.db import models
from django.utils import timezone
from core.models import User
import random
import string
import logging

logger = logging.getLogger('authentication')


class OTPCode(models.Model):
    """
    Modèle pour les codes OTP (One Time Password).
    Utilisé pour l'activation de compte et les retraits.
    """
    
    # Types d'OTP
    SIGNUP = 'signup'
    WITHDRAWAL = 'withdrawal'
    
    OTP_TYPES = [
        (SIGNUP, 'Activation de compte'),
        (WITHDRAWAL, 'Retrait d\'argent'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otp_codes',
        verbose_name="Utilisateur"
    )
    
    code = models.CharField(
        max_length=6,
        verbose_name="Code OTP"
    )
    
    otp_type = models.CharField(
        max_length=20,
        choices=OTP_TYPES,
        verbose_name="Type d'OTP"
    )
    
    is_used = models.BooleanField(
        default=False,
        verbose_name="Code utilisé"
    )
    
    expires_at = models.DateTimeField(
        verbose_name="Date d'expiration"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    class Meta:
        verbose_name = "Code OTP"
        verbose_name_plural = "Codes OTP"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['code', 'otp_type']),
        ]
    
    def __str__(self):
        return f"OTP {self.get_otp_type_display()} pour {self.user.username} - Expire: {self.expires_at}"
    
    def is_valid(self):
        """Vérifie si l'OTP est encore valide"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        """Marque l'OTP comme utilisé"""
        self.is_used = True
        self.save()
        logger.info(f"OTP utilisé: {self.otp_type} pour {self.user.username}")
    
    @staticmethod
    def generate_code(length=6):
        """Génère un code OTP aléatoire"""
        return ''.join(random.choices(string.digits, k=length))
    
    @classmethod
    def create_otp(cls, user, otp_type, expiration_minutes):
        """
        Crée un nouveau code OTP pour un utilisateur.
        
        Args:
            user: L'utilisateur concerné
            otp_type: Type d'OTP (SIGNUP ou WITHDRAWAL)
            expiration_minutes: Durée de validité en minutes
        
        Returns:
            Instance OTPCode créée
        """
        # Invalider les anciens OTP non utilisés du même type
        cls.objects.filter(
            user=user,
            otp_type=otp_type,
            is_used=False
        ).update(is_used=True)
        
        # Créer le nouveau OTP
        code = cls.generate_code()
        expires_at = timezone.now() + timezone.timedelta(minutes=expiration_minutes)
        
        otp = cls.objects.create(
            user=user,
            code=code,
            otp_type=otp_type,
            expires_at=expires_at
        )
        
        logger.info(
            f"Nouveau OTP créé: {otp_type} pour {user.username} | "
            f"Code: {code} | Expire dans {expiration_minutes} min"
        )
        
        return otp
    
    @classmethod
    def verify_otp(cls, user, code, otp_type):
        """
        Vérifie un code OTP.
        
        Args:
            user: L'utilisateur concerné
            code: Le code à vérifier
            otp_type: Type d'OTP attendu
        
        Returns:
            Tuple (bool, str): (succès, message)
        """
        try:
            otp = cls.objects.get(
                user=user,
                code=code,
                otp_type=otp_type
            )
            
            if otp.is_used:
                logger.warning(f"Tentative d'utilisation d'un OTP déjà utilisé: {user.username}")
                return False, "Ce code a déjà été utilisé."
            
            if not otp.is_valid():
                logger.warning(f"Tentative d'utilisation d'un OTP expiré: {user.username}")
                return False, "Ce code a expiré."
            
            otp.mark_as_used()
            logger.info(f"OTP vérifié avec succès: {otp_type} pour {user.username}")
            return True, "Code vérifié avec succès."
            
        except cls.DoesNotExist:
            logger.warning(f"Tentative avec un code OTP invalide: {user.username}")
            return False, "Code invalide."