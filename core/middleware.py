"""
Middleware personnalisés
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
import logging

logger = logging.getLogger(__name__)


class CheckSuspendedAccountMiddleware:
    """
    Middleware pour vérifier si un compte utilisateur est suspendu
    et le déconnecter automatiquement si c'est le cas
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Exclure les URLs qui ne nécessitent pas de vérification
        excluded_paths = [
            '/authentication/login/',
            '/authentication/signup/',
            '/authentication/verify-otp/',
            '/authentication/logout/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        # Vérifier si l'utilisateur est authentifié
        if request.user.is_authenticated:
            # Ne pas vérifier pour les superusers et le staff
            if not request.user.is_superuser and not request.user.is_staff:
                # Vérifier si l'utilisateur a un compte virtuel
                if hasattr(request.user, 'virtual_account'):
                    # Vérifier si le compte est suspendu
                    if request.user.virtual_account.is_suspended:
                        # Ne pas déconnecter sur les pages exclues
                        if not any(request.path.startswith(path) for path in excluded_paths):
                            logger.warning(f"Accès refusé pour compte suspendu: {request.user.username}")
                            logout(request)
                            messages.error(request, 'Votre compte a été suspendu. Veuillez contacter l\'administrateur.')
                            return redirect('authentication:login')
        
        response = self.get_response(request)
        return response