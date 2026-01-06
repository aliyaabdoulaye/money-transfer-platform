"""
Tests pour vérifier que toutes les vues retournent un status code 200
"""
import pytest
from django.urls import reverse
from django.test import Client


@pytest.mark.django_db
class TestPublicViews:
    """Test des vues publiques"""
    
    def test_login_view_returns_200(self):
        """Vérifier que la page de connexion retourne 200"""
        client = Client()
        response = client.get(reverse('authentication:login'))
        assert response.status_code == 200
    
    def test_signup_view_returns_200(self):
        """Vérifier que la page d'inscription retourne 200"""
        client = Client()
        response = client.get(reverse('authentication:signup'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestAuthenticatedViews:
    """Test des vues nécessitant une authentification"""
    
    def test_user_dashboard_returns_200(self, client, test_user):
        """Vérifier que le dashboard utilisateur retourne 200"""
        client.force_login(test_user)
        response = client.get(reverse('dashboard:user_dashboard'))
        assert response.status_code == 200
    
    def test_deposit_view_returns_200(self, client, test_user):
        """Vérifier que la page de dépôt retourne 200"""
        client.force_login(test_user)
        response = client.get(reverse('transactions:deposit'))
        assert response.status_code == 200
    
    def test_transfer_view_returns_200(self, client, test_user):
        """Vérifier que la page de transfert retourne 200"""
        client.force_login(test_user)
        response = client.get(reverse('transactions:transfer'))
        assert response.status_code == 200
    
    def test_withdrawal_request_view_returns_200(self, client, test_user):
        """Vérifier que la page de retrait retourne 200"""
        client.force_login(test_user)
        response = client.get(reverse('transactions:withdrawal_request'))
        assert response.status_code == 200
    
    def test_transaction_history_returns_200(self, client, test_user):
        """Vérifier que l'historique des transactions retourne 200"""
        client.force_login(test_user)
        response = client.get(reverse('transactions:history'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminViews:
    """Test des vues admin"""
    
    def test_admin_dashboard_returns_200(self, client, admin_user):
        """Vérifier que le dashboard admin retourne 200"""
        client.force_login(admin_user)
        response = client.get(reverse('dashboard:admin_dashboard'))
        assert response.status_code == 200
    
    def test_manage_users_returns_200(self, client, admin_user):
        """Vérifier que la gestion des utilisateurs retourne 200"""
        client.force_login(admin_user)
        response = client.get(reverse('dashboard:manage_users'))
        assert response.status_code == 200
    
    def test_non_admin_cannot_access_admin_dashboard(self, client, test_user):
        """Vérifier qu'un utilisateur normal ne peut pas accéder au dashboard admin"""
        client.force_login(test_user)
        response = client.get(reverse('dashboard:admin_dashboard'))
        assert response.status_code == 403