"""
Services pour la gestion des transactions financières
"""
from django.db import transaction
from django.conf import settings
from decimal import Decimal
from core.models import VirtualAccount
from .models import Transaction
import uuid
import logging

logger = logging.getLogger('transactions')


class TransactionService:
    """
    Service de base pour les opérations financières
    """
    
    @staticmethod
    def generate_reference():
        """Génère une référence unique pour une transaction"""
        return f"TXN-{uuid.uuid4().hex[:12].upper()}"
    
    @staticmethod
    def get_platform_account():
        """Récupère le compte virtuel de la plateforme"""
        try:
            platform_account = VirtualAccount.objects.get(is_platform_account=True)
            return platform_account
        except VirtualAccount.DoesNotExist:
            logger.error("Le compte plateforme n'existe pas!")
            raise Exception("Erreur système: compte plateforme introuvable")
    
    @staticmethod
    def validate_amount(amount):
        """Valide qu'un montant est positif"""
        if amount <= 0:
            return False, "Le montant doit être supérieur à zéro"
        return True, ""
    
    @staticmethod
    def check_account_status(virtual_account):
        """Vérifie si un compte peut effectuer des opérations"""
        if virtual_account.is_suspended:
            return False, "Votre compte est suspendu. Contactez l'administrateur."
        if not virtual_account.user.is_active:
            return False, "Votre compte n'est pas activé."
        return True, ""


class DepositService:
    """
    Service pour gérer les dépôts d'argent
    """
    
    @staticmethod
    @transaction.atomic
    def deposit(virtual_account, amount, description="Dépôt d'argent"):
        """
        Effectue un dépôt sur un compte virtuel
        
        Args:
            virtual_account: Le compte à créditer
            amount: Le montant à déposer
            description: Description du dépôt
        
        Returns:
            tuple: (success: bool, message: str, transaction: Transaction or None)
        """
        try:
            # Vérifier le statut du compte
            is_valid, error_msg = TransactionService.check_account_status(virtual_account)
            if not is_valid:
                return False, error_msg, None
            
            # Valider le montant
            amount = Decimal(str(amount))
            is_valid, error_msg = TransactionService.validate_amount(amount)
            if not is_valid:
                return False, error_msg, None
            
            # Créer la transaction
            txn = Transaction.objects.create(
                transaction_type=Transaction.DEPOSIT,
                amount=amount,
                sender_account=virtual_account,
                receiver_account=virtual_account,
                reference=TransactionService.generate_reference(),
                description=description,
                status=Transaction.COMPLETED
            )
            
            # Mettre à jour le solde
            virtual_account.balance += amount
            virtual_account.save()
            
            logger.info(
                f"Dépôt réussi: {amount} FCFA sur le compte de {virtual_account.user.username} | "
                f"Nouveau solde: {virtual_account.balance} FCFA | Ref: {txn.reference}"
            )
            
            return True, f"Dépôt de {amount} FCFA effectué avec succès", txn
            
        except Exception as e:
            logger.error(f"Erreur lors du dépôt: {str(e)}")
            return False, "Une erreur est survenue lors du dépôt", None


class TransferService:
    """
    Service pour gérer les transferts entre comptes
    """
    
    @staticmethod
    @transaction.atomic
    def transfer(sender_account, receiver_phone, amount, description="Transfert d'argent"):
        """
        Effectue un transfert d'argent entre deux comptes
        
        Args:
            sender_account: Le compte émetteur
            receiver_phone: Le numéro de téléphone du destinataire
            amount: Le montant à transférer
            description: Description du transfert
        
        Returns:
            tuple: (success: bool, message: str, transaction: Transaction or None)
        """
        try:
            # Vérifier le statut du compte émetteur
            is_valid, error_msg = TransactionService.check_account_status(sender_account)
            if not is_valid:
                return False, error_msg, None
            
            # Valider le montant
            amount = Decimal(str(amount))
            is_valid, error_msg = TransactionService.validate_amount(amount)
            if not is_valid:
                return False, error_msg, None
            
            # Vérifier le solde suffisant
            if sender_account.balance < amount:
                return False, "Solde insuffisant pour effectuer ce transfert", None
            
            # Trouver le compte destinataire
            try:
                from core.models import User
                receiver_user = User.objects.get(phone_number=receiver_phone, is_active=True)
                receiver_account = receiver_user.virtual_account
            except User.DoesNotExist:
                return False, "Aucun utilisateur actif trouvé avec ce numéro de téléphone", None
            except Exception:
                return False, "Le destinataire n'a pas de compte virtuel", None
            
            # Vérifier qu'on ne transfère pas à soi-même
            if sender_account.id == receiver_account.id:
                return False, "Vous ne pouvez pas transférer de l'argent à vous-même", None
            
            # Vérifier que le compte destinataire n'est pas suspendu
            if receiver_account.is_suspended:
                return False, "Le compte du destinataire est suspendu", None
            
            # Créer la transaction
            txn = Transaction.objects.create(
                transaction_type=Transaction.TRANSFER,
                amount=amount,
                sender_account=sender_account,
                receiver_account=receiver_account,
                reference=TransactionService.generate_reference(),
                description=description,
                status=Transaction.COMPLETED
            )
            
            # Mettre à jour les soldes
            sender_account.balance -= amount
            sender_account.save()
            
            receiver_account.balance += amount
            receiver_account.save()
            
            logger.info(
                f"Transfert réussi: {amount} FCFA de {sender_account.user.username} "
                f"vers {receiver_account.user.username} | Ref: {txn.reference}"
            )
            
            return True, f"Transfert de {amount} FCFA effectué avec succès vers {receiver_user.username}", txn
            
        except Exception as e:
            logger.error(f"Erreur lors du transfert: {str(e)}")
            return False, "Une erreur est survenue lors du transfert", None


class WithdrawalService:
    """
    Service pour gérer les retraits d'argent avec calcul automatique des frais
    """
    
    @staticmethod
    def calculate_fee(amount):
        """
        Calcule les frais de retrait
        
        Args:
            amount: Le montant du retrait demandé
        
        Returns:
            tuple: (withdrawal_amount: Decimal, fee_amount: Decimal)
        """
        amount = Decimal(str(amount))
        fee_percentage = Decimal(str(settings.WITHDRAWAL_FEE_PERCENTAGE)) / Decimal('100')
        fee_amount = amount * fee_percentage
        withdrawal_amount = amount - fee_amount
        
        return withdrawal_amount, fee_amount
    
    @staticmethod
    @transaction.atomic
    def withdraw(virtual_account, requested_amount, description="Retrait d'argent"):
        """
        Effectue un retrait avec calcul automatique des frais
        Génère 2 transactions : withdrawal + fee
        
        Args:
            virtual_account: Le compte à débiter
            requested_amount: Le montant demandé par l'utilisateur
            description: Description du retrait
        
        Returns:
            tuple: (success: bool, message: str, transactions: dict or None)
        """
        try:
            # Vérifier le statut du compte
            is_valid, error_msg = TransactionService.check_account_status(virtual_account)
            if not is_valid:
                return False, error_msg, None
            
            # Valider le montant
            requested_amount = Decimal(str(requested_amount))
            is_valid, error_msg = TransactionService.validate_amount(requested_amount)
            if not is_valid:
                return False, error_msg, None
            
            # Vérifier le solde suffisant
            if virtual_account.balance < requested_amount:
                return False, "Solde insuffisant pour effectuer ce retrait", None
            
            # Calculer les montants
            withdrawal_amount, fee_amount = WithdrawalService.calculate_fee(requested_amount)
            
            # Récupérer le compte plateforme
            platform_account = TransactionService.get_platform_account()
            
            # Créer la transaction de retrait
            withdrawal_txn = Transaction.objects.create(
                transaction_type=Transaction.WITHDRAWAL,
                amount=withdrawal_amount,
                sender_account=virtual_account,
                receiver_account=None,  # NULL pour les retraits
                reference=TransactionService.generate_reference(),
                description=f"{description} - Montant retiré",
                status=Transaction.COMPLETED
            )
            
            # Créer la transaction de commission
            fee_txn = Transaction.objects.create(
                transaction_type=Transaction.FEE,
                amount=fee_amount,
                sender_account=virtual_account,
                receiver_account=platform_account,
                reference=TransactionService.generate_reference(),
                description=f"{description} - Commission plateforme ({settings.WITHDRAWAL_FEE_PERCENTAGE}%)",
                status=Transaction.COMPLETED
            )
            
            # Mettre à jour les soldes
            virtual_account.balance -= requested_amount
            virtual_account.save()
            
            platform_account.balance += fee_amount
            platform_account.save()
            
            logger.info(
                f"Retrait réussi: Montant demandé: {requested_amount} FCFA | "
                f"Montant retiré: {withdrawal_amount} FCFA | Commission: {fee_amount} FCFA | "
                f"Utilisateur: {virtual_account.user.username} | "
                f"Nouveau solde: {virtual_account.balance} FCFA"
            )
            
            transactions_data = {
                'withdrawal': withdrawal_txn,
                'fee': fee_txn,
                'withdrawal_amount': withdrawal_amount,
                'fee_amount': fee_amount,
                'total_amount': requested_amount
            }
            
            return True, f"Retrait de {withdrawal_amount} FCFA effectué avec succès (frais: {fee_amount} FCFA)", transactions_data
            
        except Exception as e:
            logger.error(f"Erreur lors du retrait: {str(e)}")
            return False, "Une erreur est survenue lors du retrait", None