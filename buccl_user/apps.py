from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver

class BucclUserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'buccl_user'
    
    def ready(self):
        from . import signals

@receiver(user_logged_out)
def delete_token_on_logout(sender, request, user, **kwargs):
    response = request.META.get('HTTP_RESPONSE', None)
    if response:
        response.delete_cookie("access")
        response.delete_cookie("refresh")