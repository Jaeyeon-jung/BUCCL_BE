from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver

@receiver(user_logged_out)
def delete_token_on_logout(sender, request, user, **kwargs):
    response = request.META.get('HTTP_RESPONSE', None)
    if response:
        response.delete_cookie("access")
        response.delete_cookie("refresh")