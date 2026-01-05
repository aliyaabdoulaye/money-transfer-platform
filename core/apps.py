"""
Configuration de l'application core
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'
    
    def ready(self):
        """Importer les signals lors du démarrage de l'application"""
        import core.signals