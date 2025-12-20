from django.db import models


class Disease(models.Model):
    # Модуль Болезней

    disease_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey('self', verbose_name='Главная Болезнь', related_name='disease_child',
                               on_delete=models.SET_NULL, null=True, blank=True)
    disease_title = models.CharField(verbose_name='Название болезни', max_length=150)
    archive = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    updated_at = models.DateTimeField(verbose_name='Обновлён', auto_now=True)
    created_at = models.DateTimeField(verbose_name='Создан', auto_now_add=True)

    def __str__(self):
        return self.disease_title

    class Meta:
        verbose_name = 'Болезнь'
        verbose_name_plural = 'Болезни'
        default_permissions = ()
        permissions = [
            ('add_disease', 'Добавить болезнь'),
            ('view_disease', 'Просмотреть болезнь'),
            ('change_disease', 'Изменить болезнь'),
            ('delete_disease', 'Удалить болезнь')
        ]

