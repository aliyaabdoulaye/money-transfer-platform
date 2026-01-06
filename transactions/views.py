"""
Vues pour les transactions
"""
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from .forms import DepositForm, TransferForm, WithdrawalForm, WithdrawalOTPForm
from .services import DepositService, TransferService, WithdrawalService
from authentication.services import OTPService
from authentication.models import OTPCode
import logging

logger = logging.getLogger('transactions')


class DepositView(LoginRequiredMixin, View):
    """
    Vue pour effectuer un dépôt
    """
    template_name = 'transactions/deposit.html'
    
    def get(self, request):
        form = DepositForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = DepositForm(request.POST)
        
        if form.is_valid():
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', 'Dépôt d\'argent')
            
            # Effectuer le dépôt
            success, message, transaction = DepositService.deposit(
                request.user.virtual_account,
                amount,
                description
            )
            
            if success:
                messages.success(request, message)
                return redirect('dashboard:user_dashboard')
            else:
                messages.error(request, message)
        
        return render(request, self.template_name, {'form': form})


class TransferView(LoginRequiredMixin, View):
    """
    Vue pour effectuer un transfert
    """
    template_name = 'transactions/transfer.html'
    
    def get(self, request):
        form = TransferForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = TransferForm(request.POST)
        
        if form.is_valid():
            receiver_phone = form.cleaned_data['receiver_phone']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', 'Transfert d\'argent')
            
            # Effectuer le transfert
            success, message, transaction = TransferService.transfer(
                request.user.virtual_account,
                receiver_phone,
                amount,
                description
            )
            
            if success:
                messages.success(request, message)
                return redirect('dashboard:user_dashboard')
            else:
                messages.error(request, message)
        
        return render(request, self.template_name, {'form': form})


class WithdrawalRequestView(LoginRequiredMixin, View):
    """
    Vue pour demander un retrait (génère et envoie l'OTP)
    """
    template_name = 'transactions/withdrawal_request.html'
    
    def get(self, request):
        form = WithdrawalForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = WithdrawalForm(request.POST)
        
        if form.is_valid():
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', 'Retrait d\'argent')
            
            # Vérifier que l'utilisateur a assez de solde
            if request.user.virtual_account.balance < amount:
                messages.error(request, 'Solde insuffisant pour effectuer ce retrait.')
                return render(request, self.template_name, {'form': form})
            
            # Calculer les frais pour affichage
            withdrawal_amount, fee_amount = WithdrawalService.calculate_fee(amount)
            
            # Générer et envoyer l'OTP
            success, message, otp = OTPService.generate_and_send_otp(
                request.user,
                OTPCode.WITHDRAWAL
            )
            
            if success:
                # Stocker les infos du retrait en session
                request.session['withdrawal_data'] = {
                    'amount': str(amount),
                    'description': description,
                    'withdrawal_amount': str(withdrawal_amount),
                    'fee_amount': str(fee_amount)
                }
                messages.success(request, message)
                return redirect('transactions:withdrawal_verify')
            else:
                messages.error(request, message)
        
        return render(request, self.template_name, {'form': form})


class WithdrawalVerifyView(LoginRequiredMixin, View):
    """
    Vue pour vérifier l'OTP et finaliser le retrait
    """
    template_name = 'transactions/withdrawal_verify.html'
    
    def get(self, request):
        # Vérifier qu'il y a un retrait en attente
        if 'withdrawal_data' not in request.session:
            messages.warning(request, 'Aucun retrait en attente.')
            return redirect('transactions:withdrawal_request')
        
        form = WithdrawalOTPForm()
        withdrawal_data = request.session['withdrawal_data']
        return render(request, self.template_name, {
            'form': form,
            'withdrawal_data': withdrawal_data
        })
    
    def post(self, request):
        if 'withdrawal_data' not in request.session:
            messages.warning(request, 'Session expirée. Veuillez recommencer.')
            return redirect('transactions:withdrawal_request')
        
        form = WithdrawalOTPForm(request.POST)
        
        if form.is_valid():
            code = form.cleaned_data['otp_code']
            
            # Vérifier l'OTP
            success, message = OTPService.verify_otp(
                request.user,
                code,
                OTPCode.WITHDRAWAL
            )
            
            if success:
                # Récupérer les données du retrait
                withdrawal_data = request.session['withdrawal_data']
                amount = withdrawal_data['amount']
                description = withdrawal_data['description']
                
                # Effectuer le retrait
                success, message, transaction_data = WithdrawalService.withdraw(
                    request.user.virtual_account,
                    amount,
                    description
                )
                
                if success:
                    # Nettoyer la session
                    del request.session['withdrawal_data']
                    messages.success(request, message)
                    return redirect('dashboard:user_dashboard')
                else:
                    messages.error(request, message)
            else:
                messages.error(request, message)
        
        withdrawal_data = request.session.get('withdrawal_data', {})
        return render(request, self.template_name, {
            'form': form,
            'withdrawal_data': withdrawal_data
        })


class ResendWithdrawalOTPView(LoginRequiredMixin, View):
    """
    Vue pour renvoyer l'OTP de retrait
    """
    def post(self, request):
        if 'withdrawal_data' not in request.session:
            messages.warning(request, 'Aucun retrait en attente.')
            return redirect('transactions:withdrawal_request')
        
        # Renvoyer l'OTP
        success, message, otp = OTPService.resend_otp(
            request.user,
            OTPCode.WITHDRAWAL
        )
        
        if success:
            messages.success(request, 'Un nouveau code a été envoyé.')
        else:
            messages.error(request, message)
        
        return redirect('transactions:withdrawal_verify')


class TransactionHistoryView(LoginRequiredMixin, View):
    """
    Vue pour afficher l'historique des transactions
    """
    template_name = 'transactions/history.html'
    
    def get(self, request):
        # Récupérer toutes les transactions de l'utilisateur
        sent_transactions = request.user.virtual_account.sent_transactions.all()[:20]
        received_transactions = request.user.virtual_account.received_transactions.all()[:20]
        
        # Combiner et trier par date
        all_transactions = sorted(
            list(sent_transactions) + list(received_transactions),
            key=lambda x: x.created_at,
            reverse=True
        )[:20]
        
        context = {
            'transactions': all_transactions,
        }
        return render(request, self.template_name, context)