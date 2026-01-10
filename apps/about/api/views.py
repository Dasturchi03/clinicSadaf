from rest_framework.viewsets import ModelViewSet

from apps.about.models import Article
from apps.about.filtersets import ArticleFilterSet
from apps.about.api.serializers import ArticleCreateSerializer, ArticleOutSerializer


class ArticleViewSet(ModelViewSet):
    queryset = Article.objects.prefetch_related('images')
    filterset_class = ArticleFilterSet

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ArticleCreateSerializer
        return ArticleOutSerializer
