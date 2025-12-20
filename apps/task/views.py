from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, CreateAPIView, GenericAPIView
from .serializers import TaskSerializer, TaskCreateSerializer, TaskDoneSerializer
from apps.task.models import Task
from rest_framework.response import Response


class TaskCreateView(CreateAPIView):
    # Создание задачи

    serializer_class = TaskCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        history_signal.send(sender=Task, instance=obj, user=current_user_func(request),
                            ip=ip_current_user_func(request), created=True)
        return Response(serializer.data)


class TaskListView(ListAPIView):
    # Список задач

    serializer_class = TaskSerializer

    def get_queryset(self, *args, **kwargs):
        queryset = Task.objects.filter(task_to_id=self.kwargs.get('pk'))
        return queryset


class TaskSingleView(GenericAPIView):
    # Задача обновление + смотреть одну задачу
    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def get_object(self, *args, **kwargs):
        instance = self.queryset.get(pk=self.kwargs.get('pk'))
        return instance

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
def task_done_view(request, pk):
    instance = Task.objects.get(pk=pk)
    if instance.task_finished:
        instance.task_finished = False
        instance.save()
    else:
        instance.task_finished = True
        instance.save()
    return Response(status=status.HTTP_200_OK)

