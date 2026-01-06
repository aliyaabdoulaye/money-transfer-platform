"""
Tests pour les modèles
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from core.models import VirtualAccount
from transactions.models import Transaction

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests pour le modèle User"""
    
    def test_create_user(self, user_factory):
        """Tester la création d'un utilisateur"""
        user = user_factory(username='newuser', email='new@test.com')
        
        assert user.username == 'newuser'
        assert user.email == 'new@test.com'
        assert user.is_active is True
    
    def test_user_has_virtual_account(self, test_user):
        """Vérifier qu'un utilisateur actif a un compte virtuel"""
        assert hasattr(test_user, 'virtual_account')
        assert test_user.virtual_account is not None


@pytest.mark.django_db
class TestVirtualAccountModel:
    """Tests pour le modèle VirtualAccount"""
    
    def test_virtual_account_default_balance(self, test_user):
        """Vérifier que le solde par défaut est 0"""
        assert test_user.virtual_account.balance == Decimal('0')
    
    def test_virtual_account_can_perform_operations(self, test_user):
        """Vérifier qu'un compte actif peut effectuer des opérations"""
        assert test_user.virtual_account.can_perform_operations() is True
    
    def test_suspended_account_cannot_perform_operations(self, test_user):
        """Vérifier qu'un compte suspendu ne peut pas effectuer d'opérations"""
        test_user.virtual_account.suspend()
        assert test_user.virtual_account.can_perform_operations() is False
    
    def test_suspend_and_reactivate_account(self, test_user):
        """Tester la suspension et réactivation d'un compte"""
        # Suspendre
        test_user.virtual_account.suspend()
        test_user.virtual_account.refresh_from_db()
        assert test_user.virtual_account.is_suspended is True
        
        # Réactiver
        test_user.virtual_account.reactivate()
        test_user.virtual_account.refresh_from_db()
        assert test_user.virtual_account.is_suspended is False


@pytest.mark.django_db
class TestTransactionModel:
    """Tests pour le modèle Transaction"""
    
    def test_transaction_types_exist(self):
        """Vérifier que tous les types de transactions existent"""
        assert Transaction.DEPOSIT == 'deposit'
        assert Transaction.TRANSFER == 'transfer'
        assert Transaction.WITHDRAWAL == 'withdrawal'
        assert Transaction.FEE == 'fee'
    
    def test_calculate_total_fees(self, test_user, platform_account):
        """Tester le calcul du total des commissions"""
        from transactions.services import DepositService, WithdrawalService
        
        # Faire un dépôt puis un retrait
        DepositService.deposit(test_user.virtual_account, Decimal('50000'))
        WithdrawalService.withdraw(test_user.virtual_account, Decimal('10000'))
        
        # Le retrait de 10000 génère 200 FCFA de frais
        total_fees = Transaction.calculate_total_fees()
        assert total_fees == Decimal('200')
    
    def test_transaction_has_unique_reference(self, test_user):
        """Vérifier que chaque transaction a une référence unique"""
        from transactions.services import DepositService
        
        _, _, txn1 = DepositService.deposit(test_user.virtual_account, Decimal('1000'))
        _, _, txn2 = DepositService.deposit(test_user.virtual_account, Decimal('2000'))
        
        assert txn1.reference != txn2.reference