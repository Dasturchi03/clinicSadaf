from rest_framework import status, viewsets
from rest_framework.response import Response
from apps.core.utils import dict_for_formdata


class BaseViewSet(viewsets.GenericViewSet):

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params:
            queryset = self.filter_queryset(queryset)
        return queryset
    
    def get_object(self):
        return super().get_object()
    
    def create(self, request, *args, **kwargs):
        data = dict_for_formdata(request.data) if 'multipart/form-data' in request.content_type else request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer=serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()
    
    def list(self, request, **kwargs):
        queryset = self.get_queryset()
        if "page" not in request.query_params:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        pagination = self.pagination_class()
        result_page = pagination.paginate_queryset(queryset, request)
        serializer = self.get_serializer(result_page, many=True)
        return pagination.get_paginated_response(serializer.data)
    
    def retrieve(self, request, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer=serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer=serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def perform_update(self, serializer):
        serializer.save()
    
    def destroy(self, request, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance=instance)
        return Response({"Удаление успешно!"}, status=status.HTTP_200_OK)
    
    def perform_destroy(self, instance):
        instance.delete()
