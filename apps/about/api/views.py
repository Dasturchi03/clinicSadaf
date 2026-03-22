from drf_spectacular.utils import extend_schema
from rest_framework import mixins
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.views import BaseViewSet

from apps.core.choices import ArticleTypes
from apps.about.models import Article
from apps.about.api.serializers import (
    ArticlePublicDetailSerializer,
    ArticlePublicListSerializer,
)


@extend_schema(tags=["mobile_content"])
class ArticlePublicViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           BaseViewSet):
    permission_classes = (AllowAny,)
    queryset = Article.objects.prefetch_related("images").order_by("-created_at")
    http_method_names = ["get", "head", "options"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ArticlePublicDetailSerializer
        return ArticlePublicListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        article_type = getattr(self, "default_article_type", None) or self.request.query_params.get("article_type")
        q = self.request.query_params.get("q")

        if article_type:
            queryset = queryset.filter(article_type=article_type)
        if q:
            queryset = queryset.filter(article_title__icontains=q)
        return queryset


class NewsPublicViewSet(ArticlePublicViewSet):
    default_article_type = ArticleTypes.NEWS


@extend_schema(tags=["mobile_content"])
class MobileAboutView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        queryset = Article.objects.exclude(
            article_type=ArticleTypes.NEWS
        ).prefetch_related("images").order_by("-created_at")
        serializer_context = {"request": request}

        return Response(
            {
                "general_info": ArticlePublicListSerializer(
                    queryset.filter(article_type=ArticleTypes.GENERAL_INFO),
                    many=True,
                    context=serializer_context,
                ).data,
                "achievements": ArticlePublicListSerializer(
                    queryset.filter(article_type=ArticleTypes.ACHIEVEMENTS),
                    many=True,
                    context=serializer_context,
                ).data,
                "laboratory": ArticlePublicListSerializer(
                    queryset.filter(article_type=ArticleTypes.LABORATORY),
                    many=True,
                    context=serializer_context,
                ).data,
                "comments": ArticlePublicListSerializer(
                    queryset.filter(article_type=ArticleTypes.COMMENTS),
                    many=True,
                    context=serializer_context,
                ).data,
            }
        )
