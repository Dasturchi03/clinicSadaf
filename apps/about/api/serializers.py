from rest_framework import serializers

from apps.about.models import Article, ArticleImage
from apps.about.api.nested_serializers import NestedArticleImageSerializer


class ArticleAdminWriteSerializer(serializers.ModelSerializer):
    article_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True,
    )

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
            "article_images",
        ]
        extra_kwargs = {
            "article_id": {"read_only": True},
        }

    def create(self, validated_data):
        images = validated_data.pop("article_images", [])
        article = Article.objects.create(**validated_data)
        if images:
            ArticleImage.objects.bulk_create(
                [ArticleImage(article=article, article_image=image) for image in images]
            )
        return article

    def update(self, instance, validated_data):
        images = validated_data.pop("article_images", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if images is not None:
            instance.images.all().delete()
            if images:
                ArticleImage.objects.bulk_create(
                    [ArticleImage(article=instance, article_image=image) for image in images]
                )
        return instance


class ArticleAdminReadSerializer(serializers.ModelSerializer):
    article_type_display = serializers.CharField(
        source="get_article_type_display", read_only=True
    )
    article_images = NestedArticleImageSerializer(many=True, source="images", read_only=True)

    class Meta:
        model = Article
        fields = [
            "article_id",
            "article_type",
            "article_type_display",
            "article_title",
            "article_title_uz",
            "article_title_ru",
            "article_title_en",
            "article_body",
            "article_body_uz",
            "article_body_ru",
            "article_body_en",
            "article_images",
            "created_at",
            "updated_at",
        ]


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
