"""
Signals pour la création automatique des comptes virtuels
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, VirtualAccount
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_virtual_account(sender, instance, created, **kwargs):
    """
    Signal pour créer automatiquement un compte virtuel
    lors de l'activation d'un utilisateur
    """
    if created:
        # Ne pas créer de compte virtuel immédiatement
        # Il sera créé lors de l'activation du compte
        pass
    elif instance.is_active and not hasattr(instance, 'virtual_account'):
        # Créer le compte virtuel si l'utilisateur est activé
        # et n'a pas encore de compte virtuel
        try:
            VirtualAccount.objects.create(user=instance)
            logger.info(f"Compte virtuel créé pour l'utilisateur: {instance.username}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du compte virtuel pour {instance.username}: {str(e)}")