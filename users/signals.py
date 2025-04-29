from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, CustomUser


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Создаем профиль с полным именем из пользователя
        Profile.objects.create(user=instance, full_name=instance.full_name)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    # Сохраняем профиль каждый раз, когда сохраняется пользователь
    instance.profile.save()