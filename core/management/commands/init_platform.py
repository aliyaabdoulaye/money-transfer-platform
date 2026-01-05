"""
Commande pour initialiser la plateforme avec le compte administrateur
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import VirtualAccount

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialise la plateforme avec le compte administrateur et le compte plateforme'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Initialisation de la plateforme...'))
        
        # Créer ou récupérer le compte plateforme
        platform_user, created = User.objects.get_or_create(
            username='platform',
            defaults={
                'email': 'platform@moneytransfer.com',
                'phone_number': '+000000000000',
                'is_active': True,
                'is_staff': True,
            }
        )
        
        if created:
            platform_user.set_password('platform_secure_password_2025')
            platform_user.save()
            self.stdout.write(self.style.SUCCESS('✓ Utilisateur plateforme créé'))
        else:
            self.stdout.write(self.style.WARNING('→ Utilisateur plateforme existe déjà'))
        
        # Créer ou récupérer le compte virtuel de la plateforme
        platform_account, created = VirtualAccount.objects.get_or_create(
            user=platform_user,
            defaults={
                'is_platform_account': True,
                'balance': 0
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Compte virtuel de la plateforme créé'))
        else:
            # S'assurer que c'est bien marqué comme compte plateforme
            if not platform_account.is_platform_account:
                platform_account.is_platform_account = True
                platform_account.save()
                self.stdout.write(self.style.SUCCESS('✓ Compte marqué comme compte plateforme'))
            else:
                self.stdout.write(self.style.WARNING('→ Compte virtuel de la plateforme existe déjà'))
        
        # Créer un superuser admin si nécessaire
        admin_exists = User.objects.filter(is_superuser=True).exclude(username='platform').exists()
        
        if not admin_exists:
            self.stdout.write(self.style.WARNING('\nCréation d\'un compte administrateur...'))
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@moneytransfer.com',
                password='admin123',
                phone_number='+228000000001',
            )
            VirtualAccount.objects.create(user=admin_user)
            self.stdout.write(self.style.SUCCESS('✓ Compte administrateur créé'))
            self.stdout.write(self.style.SUCCESS('  Username: admin'))
            self.stdout.write(self.style.SUCCESS('  Password: admin123'))
        else:
            self.stdout.write(self.style.WARNING('\n→ Un compte administrateur existe déjà'))
        
        # Afficher le résumé
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('PLATEFORME INITIALISÉE AVEC SUCCÈS'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'\nCompte plateforme: {platform_account}')
        self.stdout.write(f'Solde: {platform_account.balance} FCFA')
        self.stdout.write(self.style.SUCCESS('\nVous pouvez maintenant utiliser la plateforme!'))