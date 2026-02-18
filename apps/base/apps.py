from django.apps import AppConfig


class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.base'

    def ready(self):
        from settings.logging import setup_logging

        setup_logging()