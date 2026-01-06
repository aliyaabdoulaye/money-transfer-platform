"""
Tests pour les opérations de transactions
"""
import pytest
from decimal import Decimal
from transactions.services import DepositService, TransferService, WithdrawalService
from transactions.models import Transaction


@pytest.mark.django_db
class TestDepositService:
    """Tests pour le service de dépôt"""
    
    def test_deposit_on_virtual_account(self, test_user):
        """Tester le dépôt d'argent sur un compte virtuel"""
        # Récupérer le solde initial
        initial_balance = test_user.virtual_account.balance
        
        # Effectuer un dépôt de 10000 FCFA
        success, message, transaction = DepositService.deposit(
            test_user.virtual_account,
            Decimal('10000'),
            'Test deposit'
        )
        
        # Vérifications
        assert success is True
        assert transaction is not None
        assert transaction.transaction_type == Transaction.DEPOSIT
        assert transaction.amount == Decimal('10000')
        
        # Vérifier que le solde a été mis à jour
        test_user.virtual_account.refresh_from_db()
        assert test_user.virtual_account.balance == initial_balance + Decimal('10000')
    
    def test_deposit_creates_transaction(self, test_user):
        """Vérifier qu'un dépôt crée une transaction"""
        initial_count = Transaction.objects.count()
        
        DepositService.deposit(
            test_user.virtual_account,
            Decimal('5000'),
            'Test deposit'
        )
        
        assert Transaction.objects.count() == initial_count + 1
    
    def test_deposit_negative_amount_fails(self, test_user):
        """Vérifier qu'un dépôt avec montant négatif échoue"""
        success, message, transaction = DepositService.deposit(
            test_user.virtual_account,
            Decimal('-1000'),
            'Invalid deposit'
        )
        
        assert success is False
        assert transaction is None


@pytest.mark.django_db
class TestTransferService:
    """Tests pour le service de transfert"""
    
    def test_transfer_between_accounts(self, test_user, test_user2):
        """Tester le transfert d'argent entre deux comptes"""
        # Faire un dépôt initial sur le compte émetteur
        DepositService.deposit(test_user.virtual_account, Decimal('50000'))
        
        # Sauvegarder les soldes initiaux
        sender_initial = test_user.virtual_account.balance
        receiver_initial = test_user2.virtual_account.balance
        
        # Effectuer le transfert
        success, message, transaction = TransferService.transfer(
            test_user.virtual_account,
            test_user2.phone_number,
            Decimal('10000'),
            'Test transfer'
        )
        
        # Vérifications
        assert success is True
        assert transaction is not None
        assert transaction.transaction_type == Transaction.TRANSFER
        
        # Vérifier les soldes
        test_user.virtual_account.refresh_from_db()
        test_user2.virtual_account.refresh_from_db()
        
        assert test_user.virtual_account.balance == sender_initial - Decimal('10000')
        assert test_user2.virtual_account.balance == receiver_initial + Decimal('10000')
    
    def test_transfer_insufficient_balance_fails(self, test_user, test_user2):
        """Vérifier qu'un transfert sans solde suffisant échoue"""
        success, message, transaction = TransferService.transfer(
            test_user.virtual_account,
            test_user2.phone_number,
            Decimal('999999'),
            'Invalid transfer'
        )
        
        assert success is False
        assert transaction is None
    
    def test_transfer_to_self_fails(self, test_user):
        """Vérifier qu'un transfert à soi-même échoue"""
        DepositService.deposit(test_user.virtual_account, Decimal('10000'))
        
        success, message, transaction = TransferService.transfer(
            test_user.virtual_account,
            test_user.phone_number,
            Decimal('1000'),
            'Self transfer'
        )
        
        assert success is False
        assert transaction is None


@pytest.mark.django_db
class TestWithdrawalService:
    """Tests pour le service de retrait"""
    
    def test_withdrawal_from_virtual_account(self, test_user, platform_account):
        """Tester le retrait d'argent depuis un compte virtuel"""
        # Faire un dépôt initial
        DepositService.deposit(test_user.virtual_account, Decimal('50000'))
        
        initial_balance = test_user.virtual_account.balance
        initial_platform_balance = platform_account.balance
        
        # Effectuer un retrait de 10000 FCFA
        success, message, data = WithdrawalService.withdraw(
            test_user.virtual_account,
            Decimal('10000'),
            'Test withdrawal'
        )
        
        # Vérifications
        assert success is True
        assert data is not None
        assert 'withdrawal' in data
        assert 'fee' in data
        
        # Vérifier les montants
        withdrawal_amount = data['withdrawal_amount']
        fee_amount = data['fee_amount']
        
        assert withdrawal_amount == Decimal('9800')  # 10000 - 2% = 9800
        assert fee_amount == Decimal('200')  # 2% de 10000
        
        # Vérifier les soldes
        test_user.virtual_account.refresh_from_db()
        platform_account.refresh_from_db()
        
        assert test_user.virtual_account.balance == initial_balance - Decimal('10000')
        assert platform_account.balance == initial_platform_balance + fee_amount
    
    def test_withdrawal_creates_two_transactions(self, test_user, platform_account):
        """Vérifier qu'un retrait crée deux transactions (withdrawal + fee)"""
        DepositService.deposit(test_user.virtual_account, Decimal('50000'))
        
        initial_count = Transaction.objects.count()
        
        WithdrawalService.withdraw(
            test_user.virtual_account,
            Decimal('5000')
        )
        
        # Vérifier qu'on a bien créé 2 transactions
        assert Transaction.objects.count() == initial_count + 2
        
        # Vérifier qu'on a une transaction de retrait et une de frais
        withdrawal_txn = Transaction.objects.filter(
            transaction_type=Transaction.WITHDRAWAL
        ).last()
        fee_txn = Transaction.objects.filter(
            transaction_type=Transaction.FEE
        ).last()
        
        assert withdrawal_txn is not None
        assert fee_txn is not None
        assert withdrawal_txn.amount == Decimal('4900')  # 5000 - 2%
        assert fee_txn.amount == Decimal('100')  # 2% de 5000
    
    def test_withdrawal_fee_calculation(self, test_user):
        """Vérifier le calcul correct des frais de retrait (2%)"""
        test_amounts = [
            (Decimal('10000'), Decimal('9800'), Decimal('200')),
            (Decimal('5000'), Decimal('4900'), Decimal('100')),
            (Decimal('1000'), Decimal('980'), Decimal('20')),
        ]
        
        for requested, expected_withdrawal, expected_fee in test_amounts:
            withdrawal_amount, fee_amount = WithdrawalService.calculate_fee(requested)
            assert withdrawal_amount == expected_withdrawal
            assert fee_amount == expected_fee