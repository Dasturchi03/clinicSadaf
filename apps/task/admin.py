from django.contrib import admin
from .models import Task


class TaskAdmin(admin.ModelAdmin):
    # Админка задачи

    list_display = ['task_to', 'task_description', 'task_priority', 'task_deadline']
    search_fields = ['task_to__doctor_firstname', 'task_description']


admin.site.register(Task, TaskAdmin)
