from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError


class Command(createsuperuser.Command):
    help = 'Créer un superuser avec is_active=True automatiquement'

    def handle(self, *args, **options):
        # Appeler la commande parent
        super().handle(*args, **options)
        
        # Récupérer le dernier superuser créé et l'activer
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        username = options.get('username')
        if username:
            user = User.objects.get(username=username)
            if not user.is_active:
                user.is_active = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Superuser {username} activé automatiquement'
                    )
                )