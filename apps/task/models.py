from django.db import models
from apps.user.models import User


class Task(models.Model):
    # Модуль задач

    PRIORITY = (
        ('Высокий', 'Высокий'),
        ('Низкий', 'Низкий'),
        ('Обычный', 'Обычный'),
    )
    task_id = models.AutoField(primary_key=True)
    task_from = models.ForeignKey(User, verbose_name='От кого Задача',
                                  on_delete=models.SET_NULL, related_name='task_from', null=True)
    task_to = models.ForeignKey(User, verbose_name='Для кого Задача',
                                on_delete=models.SET_NULL,  related_name='task_to', null=True)
    task_description = models.TextField(verbose_name='Содержание Задачи')
    task_priority = models.CharField(verbose_name='Приоритет Задачи', max_length=50, choices=PRIORITY, default='Обычный')
    task_deadline = models.DateTimeField(verbose_name='Дедлайн Задачи')
    task_finished = models.BooleanField(verbose_name='Сделано', default=False)

    archive = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(verbose_name='Обновлён', auto_now=True)
    created_at = models.DateTimeField(verbose_name='Создан', auto_now_add=True)
    
    def __str__(self):
        return f"{self.task_from} + {self.task_description}"

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        default_permissions = ()
        permissions = [
            ("add_task", "Добавить задачу"),
            ("view_task", "Просмотреть задачу"),
            ("change_task", "Изменить задачу"),
            ("delete_task", "Удалить задачу")
        ]
