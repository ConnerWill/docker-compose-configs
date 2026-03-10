from django.apps import AppConfig


class AdmintoolsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admintools"

    def ready(self):
        import admintools.signals
