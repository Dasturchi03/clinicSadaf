from django.db import models


class Specialization(models.Model):
    # Модуль Специализаций

    specialization_id = models.AutoField(primary_key=True)
    specialization_text = models.CharField(verbose_name='Название специализации', max_length=255)
    updated_at = models.DateTimeField(verbose_name='Обновлён', auto_now=True)
    created_at = models.DateTimeField(verbose_name='Создан', auto_now_add=True)

    def __str__(self):
        return self.specialization_text

    class Meta:
        verbose_name = 'Специализация'
        verbose_name_plural = 'Специализации'
        default_permissions = ()
        permissions = [
            ('add_specialization', 'Добавить специализацию'),
            ('view_specialization', 'Просмотреть специализацию'),
            ('change_specialization', 'Изменить специализацию'),
            ('delete_specialization', 'Удалить специализацию')
        ]