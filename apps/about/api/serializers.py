from rest_framework import serializers

from apps.about.models import Article
from apps.about.api.nested_serializers import NestedArticleImageSerializer


class ArticlePublicListSerializer(serializers.ModelSerializer):
    article_type_display = serializers.CharField(source="get_article_type_display", read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "article_id",
            "article_type",
            "article_type_display",
            "article_title",
            "article_body",
            "cover_image",
            "created_at",
        ]
        extra_kwargs = {
            "article_title": {"read_only": True},
            "article_body": {"read_only": True},
        }

    def get_cover_image(self, obj):
        image = obj.images.first()
        if not image or not image.article_image:
            return None
        request = self.context.get("request")
        image_url = image.article_image.url
        if request:
            return request.build_absolute_uri(image_url)
        return image_url


class ArticlePublicDetailSerializer(serializers.ModelSerializer):
    article_type_display = serializers.CharField(source="get_article_type_display", read_only=True)
    article_images = NestedArticleImageSerializer(many=True, required=False, source="images")

    class Meta:
        model = Article
        fields = [
            "article_id",
            "article_type",
            "article_type_display",
            "article_title",
            "article_body",
            "article_images",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "article_title": {"read_only": True},
            "article_body": {"read_only": True},
        }
