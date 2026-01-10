from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.about.models import ArticleImage


@receiver(post_delete, sender=ArticleImage)
def delete_article_image_file(sender, instance, **kwargs):
    if instance.article_image:
        instance.article_image.delete(save=False)
