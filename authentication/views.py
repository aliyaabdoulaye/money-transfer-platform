"""
Vues pour l'authentification
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import SignupForm, OTPVerificationForm, LoginForm
from .services import OTPService
from .models import OTPCode
from core.models import VirtualAccount
import logging

logger = logging.getLogger('authentication')


class SignupView(View):
    """
    Vue pour l'inscription d'un nouvel utilisateur
    """
    template_name = 'authentication/signup.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:user_dashboard')
        form = SignupForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            # Créer l'utilisateur (non activé)
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            # Générer et envoyer l'OTP
            success, message, otp = OTPService.generate_and_send_otp(user, OTPCode.SIGNUP)
            
            if success:
                # Stocker l'ID de l'utilisateur en session pour la vérification OTP
                request.session['pending_user_id'] = user.id
                messages.success(request, message)
                logger.info(f"Inscription initiée pour {user.username}")
                return redirect('authentication:verify_otp')
            else:
                # Supprimer l'utilisateur si l'envoi d'email échoue
                user.delete()
                messages.error(request, message)
        
        return render(request, self.template_name, {'form': form})


class VerifyOTPView(View):
    """
    Vue pour vérifier le code OTP et activer le compte
    """
    template_name = 'authentication/verify_otp.html'
    
    def get(self, request):
        # Vérifier qu'il y a un utilisateur en attente d'activation
        if 'pending_user_id' not in request.session:
            messages.warning(request, 'Aucune inscription en attente.')
            return redirect('authentication:signup')
        
        form = OTPVerificationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        if 'pending_user_id' not in request.session:
            messages.warning(request, 'Session expirée. Veuillez vous réinscrire.')
            return redirect('authentication:signup')
        
        form = OTPVerificationForm(request.POST)
        
        if form.is_valid():
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            try:
                user = User.objects.get(id=request.session['pending_user_id'])
                code = form.cleaned_data['otp_code']
                
                # Vérifier l'OTP
                success, message = OTPService.verify_otp(user, code, OTPCode.SIGNUP)
                
                if success:
                    # Activer l'utilisateur
                    user.is_active = True
                    user.save()
                    
                    # Créer le compte virtuel si nécessaire
                    if not hasattr(user, 'virtual_account'):
                        VirtualAccount.objects.create(user=user)
                    
                    # Nettoyer la session
                    del request.session['pending_user_id']
                    
                    messages.success(request, 'Compte activé avec succès ! Vous pouvez maintenant vous connecter.')
                    logger.info(f"Compte activé avec succès: {user.username}")
                    return redirect('authentication:login')
                else:
                    messages.error(request, message)
            
            except User.DoesNotExist:
                messages.error(request, 'Utilisateur introuvable.')
                del request.session['pending_user_id']
                return redirect('authentication:signup')
        
        return render(request, self.template_name, {'form': form})


class ResendOTPView(View):
    """
    Vue pour renvoyer un code OTP
    """
    def post(self, request):
        if 'pending_user_id' not in request.session:
            messages.warning(request, 'Aucune inscription en attente.')
            return redirect('authentication:signup')
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=request.session['pending_user_id'])
            success, message, otp = OTPService.resend_otp(user, OTPCode.SIGNUP)
            
            if success:
                messages.success(request, 'Un nouveau code a été envoyé.')
            else:
                messages.error(request, message)
        
        except User.DoesNotExist:
            messages.error(request, 'Utilisateur introuvable.')
            del request.session['pending_user_id']
            return redirect('authentication:signup')
        
        return redirect('authentication:verify_otp')


class LoginView(View):
    """
    Vue pour la connexion
    """
    template_name = 'authentication/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:user_dashboard')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = LoginForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Vérifier si le compte est suspendu
                    if hasattr(user, 'virtual_account') and user.virtual_account.is_suspended:
                        messages.error(request, 'Votre compte est suspendu. Contactez l\'administrateur.')
                        logger.warning(f"Tentative de connexion sur compte suspendu: {username}")
                    else:
                        login(request, user)
                        messages.success(request, f'Bienvenue {user.username} !')
                        logger.info(f"Connexion réussie: {username}")
                        
                        # Redirection selon le rôle
                        if user.is_staff:
                            return redirect('dashboard:admin_dashboard')
                        return redirect('dashboard:user_dashboard')
                else:
                    messages.error(request, 'Votre compte n\'est pas activé.')
            else:
                messages.error(request, 'Identifiants incorrects.')
        
        return render(request, self.template_name, {'form': form})


class LogoutView(LoginRequiredMixin, View):
    """
    Vue pour la déconnexion
    """
    def get(self, request):
        username = request.user.username
        logout(request)
        messages.success(request, 'Vous avez été déconnecté avec succès.')
        logger.info(f"Déconnexion: {username}")
        return redirect('authentication:login')