"""
Services pour la gestion des OTP
"""
from django.core.mail import send_mail
from django.conf import settings
from .models import OTPCode
import logging

logger = logging.getLogger('authentication')


class OTPService:
    """
    Service pour gérer la création, l'envoi et la vérification des codes OTP
    """
    
    @staticmethod
    def generate_and_send_otp(user, otp_type):
        """
        Génère et envoie un code OTP à l'utilisateur
        
        Args:
            user: L'utilisateur concerné
            otp_type: Type d'OTP (SIGNUP ou WITHDRAWAL)
        
        Returns:
            tuple: (success: bool, message: str, otp: OTPCode or None)
        """
        try:
            # Déterminer la durée d'expiration selon le type
            if otp_type == OTPCode.SIGNUP:
                expiration_minutes = settings.OTP_EXPIRATION_MINUTES_SIGNUP
                subject = "Activation de votre compte"
                action = "activer votre compte"
            elif otp_type == OTPCode.WITHDRAWAL:
                expiration_minutes = settings.OTP_EXPIRATION_MINUTES_WITHDRAWAL
                subject = "Code de sécurité pour votre retrait"
                action = "confirmer votre retrait"
            else:
                return False, "Type d'OTP invalide", None
            
            # Créer l'OTP
            otp = OTPCode.create_otp(user, otp_type, expiration_minutes)
            
            # Préparer le message email
            message = f"""
Bonjour {user.username},

Votre code de sécurité pour {action} est : {otp.code}

Ce code est valide pendant {expiration_minutes} minute(s).

Si vous n'avez pas demandé ce code, veuillez ignorer ce message.

Cordialement,
L'équipe {settings.PLATFORM_NAME}
            """
            
            # Envoyer l'email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"OTP envoyé par email à {user.email} pour {otp_type}")
            return True, f"Un code a été envoyé à {user.email}", otp
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'OTP à {user.username}: {str(e)}")
            return False, "Erreur lors de l'envoi du code. Veuillez réessayer.", None
    
    @staticmethod
    def verify_otp(user, code, otp_type):
        """
        Vérifie un code OTP
        
        Args:
            user: L'utilisateur concerné
            code: Le code à vérifier
            otp_type: Type d'OTP attendu
        
        Returns:
            tuple: (success: bool, message: str)
        """
        return OTPCode.verify_otp(user, code, otp_type)
    
    @staticmethod
    def resend_otp(user, otp_type):
        """
        Renvoie un nouveau code OTP
        
        Args:
            user: L'utilisateur concerné
            otp_type: Type d'OTP
        
        Returns:
            tuple: (success: bool, message: str)
        """
        logger.info(f"Renvoi d'OTP demandé pour {user.username} - Type: {otp_type}")
        return OTPService.generate_and_send_otp(user, otp_type)