from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import ActivityLog

@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance,
            action='add_user',
            description=f'User {instance.username} registered through admin.'
        )

@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    ActivityLog.objects.create(
        user=None,  # Assuming no direct user reference is needed or using a system/placeholder user.
        action='remove_user',
        description=f'User {instance.username} deleted from admin.',
        deleted_user=instance.username  # Storing the username of the deleted user.
    )
