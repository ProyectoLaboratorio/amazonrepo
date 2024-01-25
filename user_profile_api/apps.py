from django.apps import AppConfig

class UserProfileApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_profile_api'
    
    def ready(self):
        import user_profile_api.signals