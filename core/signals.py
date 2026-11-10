from django.db.models.signals import pre_save
from django.dispatch import receiver
from rest_framework.exceptions import ValidationError
from .models import Attachment


@receiver(pre_save, sender=Attachment)
def limit_attachments(sender, instance, **kwargs):
    if instance.pk is None:
        count = Attachment.objects.filter(ticket=instance.ticket).count()
        if count >= 3:
            raise ValidationError('Максимум 3 вложения на заявку')
