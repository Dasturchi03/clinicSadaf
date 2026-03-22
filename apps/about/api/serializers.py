from rest_framework import serializers
from django.utils.translation import get_language

from apps.about.models import Article, ArticleImage
from apps.about.api.nested_serializers import NestedArticleImageSerializer


class ArticleCreateSerializer(serializers.ModelSerializer):
    article_images = serializers.ListField(child=serializers.ImageField(), required=False, allow_empty=True)

    class Meta:
        model = Article
        fields = [
            "article_id",
            "article_type",
            "article_title_uz",
            "article_title_ru",
            "article_title_en",
            "article_body_uz",
            "article_body_ru",
            "article_body_en",
            "article_images"
        ]
        extra_kwargs = {
            "article_title": {"read_only": True},
            "article_body": {"read_only": True}
        }

    def create(self, validated_data):

        article = Article.objects.create(
            article_type=validated_data.get("article_type"),
            article_title_uz=validated_data.get("article_title_uz", None),
            article_title_ru=validated_data.get("article_title_ru", None),
            article_title_en=validated_data.get("article_title_en", None),
            article_body_uz=validated_data.get("article_body_uz", None),
            article_body_ru=validated_data.get("article_body_ru", None),
            article_body_en=validated_data.get("article_body_en", None),
        )

        images = validated_data.pop("article_images", None)
        if images:
            ArticleImage.objects.bulk_create(
                [ArticleImage(article=article, article_image=img) for img in images]
            )

        return article

    def update(self, instance, validated_data):
        instance.article_type = validated_data.get(
            'article_type', instance.article_type
        )
        instance.article_title_uz = validated_data.get(
            'article_title_uz', instance.article_title_uz
        )
        instance.article_title_ru = validated_data.get(
            'article_title_ru', instance.article_title_ru
        )
        instance.article_title_en = validated_data.get(
            'article_title_en', instance.article_title_en
        )
        instance.article_body_uz = validated_data.get(
            'article_body_uz', instance.article_body_uz
        )
        instance.article_body_ru = validated_data.get(
            'article_body_ru', instance.article_body_ru
        )
        instance.article_body_en = validated_data.get(
            'article_body_en', instance.article_body_en
        )

        images = validated_data.pop('article_images', None)
        if images:
            instance.images.clear()
            ArticleImage.objects.bulk_create(
                [ArticleImage(article=instance, article_image=img) for img in images]
            )
        instance.save()
        return instance


class ArticleOutSerializer(serializers.ModelSerializer):
    article_images = NestedArticleImageSerializer(many=True, required=False, source='images')
    article_type_display = serializers.CharField(source="get_article_type_display", read_only=True)

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
            "updated_at"
        ]
        extra_kwargs = {
            "article_title": {"read_only": True},
            "article_body": {"read_only": True}
        }

    def get_article_title(self, obj):
        lang = get_language()
        return getattr(obj, 'article_title_' + lang, None) or obj.article_title

    def get_article_body(self, obj):
        lang = get_language()
        return getattr(obj, 'article_body_' + lang, None) or obj.article_body


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
