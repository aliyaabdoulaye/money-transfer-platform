"""
Configuration globale pour pytest
"""
import pytest
from django.contrib.auth import get_user_model
from core.models import VirtualAccount

User = get_user_model()


@pytest.fixture
def user_factory(db):
    """Factory pour créer des utilisateurs de test"""
    def create_user(username='testuser', email='test@example.com', 
                   phone_number='+228111111111', is_active=True, **kwargs):
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpass123',
            phone_number=phone_number,
            is_active=is_active,
            **kwargs
        )
        if is_active:
            VirtualAccount.objects.get_or_create(user=user)
        return user
    return create_user


@pytest.fixture
def test_user(user_factory):
    """Utilisateur de test simple"""
    return user_factory()


@pytest.fixture
def test_user2(user_factory):
    """Deuxième utilisateur de test"""
    return user_factory(
        username='testuser2',
        email='test2@example.com',
        phone_number='+228222222222'
    )


@pytest.fixture
def admin_user(user_factory):
    """Utilisateur admin de test"""
    return user_factory(
        username='admin',
        email='admin@test.com',
        phone_number='+228999999999',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def platform_account(db):
    """Compte plateforme de test"""
    platform_user, created = User.objects.get_or_create(
        username='platform',
        defaults={
            'email': 'platform@test.com',
            'phone_number': '+000000000000',
            'is_active': True,
        }
    )
    account, created = VirtualAccount.objects.get_or_create(
        user=platform_user,
        defaults={'is_platform_account': True}
    )
    return account