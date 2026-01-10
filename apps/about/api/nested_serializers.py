from rest_framework import serializers

from apps.about.models import ArticleImage


class NestedArticleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleImage
        fields = ["photo_id", "article_image"]
