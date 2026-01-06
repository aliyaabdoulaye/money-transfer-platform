"""
Vues pour les dashboards
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.contrib.auth import get_user_model
from core.models import VirtualAccount
from transactions.models import Transaction
from django.db.models import Count, Sum, Q
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class UserDashboardView(LoginRequiredMixin, View):
    """
    Dashboard pour les utilisateurs normaux
    """
    template_name = 'dashboard/user_dashboard.html'
    
    def get(self, request):
        # Récupérer les dernières transactions
        sent_transactions = request.user.virtual_account.sent_transactions.all()[:5]
        received_transactions = request.user.virtual_account.received_transactions.all()[:5]
        
        # Combiner et trier
        recent_transactions = sorted(
            list(sent_transactions) + list(received_transactions),
            key=lambda x: x.created_at,
            reverse=True
        )[:5]
        
        context = {
            'recent_transactions': recent_transactions,
        }
        return render(request, self.template_name, context)


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Dashboard pour les administrateurs
    """
    template_name = 'dashboard/admin_dashboard.html'
    
    def test_func(self):
        """Vérifier que l'utilisateur est admin"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request):
        # Statistiques utilisateurs
        total_users = User.objects.filter(is_staff=False).count()
        active_accounts = VirtualAccount.objects.filter(
            is_suspended=False,
            is_platform_account=False
        ).count()
        suspended_accounts = VirtualAccount.objects.filter(
            is_suspended=True,
            is_platform_account=False
        ).count()
        
        # Statistiques transactions
        total_transactions = Transaction.objects.filter(status=Transaction.COMPLETED).count()
        total_volume = Transaction.objects.filter(
            status=Transaction.COMPLETED
        ).exclude(
            transaction_type=Transaction.FEE
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Calcul des commissions
        total_fees = Transaction.objects.filter(
            transaction_type=Transaction.FEE,
            status=Transaction.COMPLETED
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Transactions par type
        transactions_by_type = Transaction.objects.filter(
            status=Transaction.COMPLETED
        ).values('transaction_type').annotate(count=Count('id'))
        
        # Dernières transactions
        recent_transactions = Transaction.objects.filter(
            status=Transaction.COMPLETED
        ).select_related(
            'sender_account__user',
            'receiver_account__user'
        ).order_by('-created_at')[:10]
        
        # Utilisateurs récents
        recent_users = User.objects.filter(
            is_staff=False
        ).order_by('-date_joined')[:5]
        
        context = {
            'total_users': total_users,
            'active_accounts': active_accounts,
            'suspended_accounts': suspended_accounts,
            'total_transactions': total_transactions,
            'total_volume': total_volume,
            'total_fees': total_fees,
            'transactions_by_type': transactions_by_type,
            'recent_transactions': recent_transactions,
            'recent_users': recent_users,
        }
        return render(request, self.template_name, context)


class ManageUsersView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Vue pour gérer tous les utilisateurs
    """
    template_name = 'dashboard/manage_users.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request):
        # Récupérer tous les utilisateurs (sauf staff et plateforme)
        users = User.objects.filter(
            is_staff=False
        ).select_related('virtual_account').order_by('-date_joined')
        
        # Filtrer par statut si demandé
        status_filter = request.GET.get('status')
        if status_filter == 'active':
            users = users.filter(virtual_account__is_suspended=False)
        elif status_filter == 'suspended':
            users = users.filter(virtual_account__is_suspended=True)
        
        context = {
            'users': users,
            'status_filter': status_filter,
        }
        return render(request, self.template_name, context)


class SuspendUserView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Vue pour suspendre un utilisateur
    """
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id, is_staff=False)
        
        if hasattr(user, 'virtual_account'):
            if user.virtual_account.is_platform_account:
                messages.error(request, 'Impossible de suspendre le compte plateforme.')
            elif user.virtual_account.is_suspended:
                messages.warning(request, f'Le compte de {user.username} est déjà suspendu.')
            else:
                user.virtual_account.suspend()
                messages.success(request, f'Le compte de {user.username} a été suspendu avec succès.')
                logger.warning(f"Admin {request.user.username} a suspendu le compte de {user.username}")
        else:
            messages.error(request, 'Cet utilisateur n\'a pas de compte virtuel.')
        
        return redirect('dashboard:manage_users')


class ReactivateUserView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Vue pour réactiver un utilisateur suspendu
    """
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id, is_staff=False)
        
        if hasattr(user, 'virtual_account'):
            if not user.virtual_account.is_suspended:
                messages.warning(request, f'Le compte de {user.username} n\'est pas suspendu.')
            else:
                user.virtual_account.reactivate()
                messages.success(request, f'Le compte de {user.username} a été réactivé avec succès.')
                logger.info(f"Admin {request.user.username} a réactivé le compte de {user.username}")
        else:
            messages.error(request, 'Cet utilisateur n\'a pas de compte virtuel.')
        
        return redirect('dashboard:manage_users')


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Vue pour voir les détails d'un utilisateur
    """
    template_name = 'dashboard/user_detail.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        
        # Récupérer les transactions de l'utilisateur
        if hasattr(user, 'virtual_account'):
            sent_transactions = user.virtual_account.sent_transactions.all()[:20]
            received_transactions = user.virtual_account.received_transactions.all()[:20]
            
            all_transactions = sorted(
                list(sent_transactions) + list(received_transactions),
                key=lambda x: x.created_at,
                reverse=True
            )[:20]
            
            # Statistiques
            total_sent = user.virtual_account.sent_transactions.filter(
                status=Transaction.COMPLETED
            ).exclude(
                transaction_type=Transaction.FEE
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            total_received = user.virtual_account.received_transactions.filter(
                status=Transaction.COMPLETED
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            total_fees_paid = user.virtual_account.sent_transactions.filter(
                transaction_type=Transaction.FEE,
                status=Transaction.COMPLETED
            ).aggregate(Sum('amount'))['amount__sum'] or 0
        else:
            all_transactions = []
            total_sent = 0
            total_received = 0
            total_fees_paid = 0
        
        context = {
            'user_detail': user,
            'transactions': all_transactions,
            'total_sent': total_sent,
            'total_received': total_received,
            'total_fees_paid': total_fees_paid,
        }
        return render(request, self.template_name, context)