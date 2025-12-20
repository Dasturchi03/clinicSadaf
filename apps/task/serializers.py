from rest_framework import serializers
from apps.user.models import User
from apps.task.models import Task


class TaskCreateSerializer(serializers.ModelSerializer):
    # Создание задач

    task_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    task_from = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    task_deadline = serializers.DateTimeField(format='%d-%m-%YT%H:%M', input_formats=["%d-%m-%YT%H:%M"])

    class Meta:
        model = Task
        fields = ['task_to', 'task_from', 'task_description', 'task_priority', 'task_deadline']


class TaskSerializer(serializers.ModelSerializer):
    # Список задач
    task_deadline = serializers.DateTimeField(format='%d-%m-%YT%H:%M', input_formats=["%d-%m-%YT%H:%M"], required=False)

    class Meta:
        model = Task
        fields = ['task_id', 'task_to', 'task_from', 'task_description', 'task_priority', 'task_deadline',
                  'task_finished']
        extra_kwargs = {'task_id': {'read_only': True}, 'task_to': {'required': False},
                        'task_from': {'required': False}, 'task_description': {'required': False},
                        'task_priority': {'required': False}, 'task_finished': {'read_only': True}}

    def update(self, instance, validated_data):
        instance.task_to = validated_data.get('task_to', instance.task_to)
        instance.task_description = validated_data.get('task_description', instance.task_description)
        instance.task_priority = validated_data.get('task_priority', instance.task_priority)
        instance.task_deadline = validated_data.get('task_deadline', instance.task_deadline)
        instance.save()
        return instance


class TaskDoneSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = ['task_finished']

