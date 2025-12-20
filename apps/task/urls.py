from django.urls import path
from .views import (TaskListView, TaskCreateView, TaskSingleView)
from . import views
app_name = 'task'


urlpatterns = [

    # Создание задач
    path('task_create/', TaskCreateView.as_view(), name='task_create'),

    # Задача + обновление
    path('task_single/<int:pk>/', TaskSingleView.as_view(), name='task_single'),

    # Список задач
    path('task_list/<int:pk>/', TaskListView.as_view(), name='task_list'),

    # Задача закончена
    path('task_done/<int:pk>/', views.task_done_view, name='task_done'),

]
