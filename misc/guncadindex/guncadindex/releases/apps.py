from django.apps import AppConfig


class ReleasesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "releases"

    def ready(self):
        import releases.signals
