from django.http import FileResponse, Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.views import APIView

from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.core.permissions import AccessPermissions

from apps.core.choices import ArticleTypes
from apps.about.models import Article, ContractDocument, TermsAndConditions, Contacts
from apps.about.api.serializers import (
    ArticleAdminReadSerializer,
    ArticleAdminWriteSerializer,
    ArticlePublicDetailSerializer,
    ArticlePublicListSerializer,
    TermsQuerySerializer,
    TermsAndConditionsSerializer,
    ContactsSerializer
)


@extend_schema(tags=["articles"])
class ArticleViewSet(BaseViewSet):
    queryset = Article.objects.prefetch_related("images").order_by("-created_at")
    permission_classes = (AccessPermissions,)
    pagination_class = BasePagination
    lookup_field = "article_id"

    def get_serializer_class(self):
        if self.action in ("create", "partial_update", "update"):
            return ArticleAdminWriteSerializer
        return ArticleAdminReadSerializer


@extend_schema(
    tags=["mobile_content"],
    parameters=[
        OpenApiParameter(
            name="article_type",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Optional article type filter for public articles.",
        ),
        OpenApiParameter(
            name="q",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Search by article title.",
        ),
    ],
)
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


@extend_schema(
    tags=["mobile_content"],
)
class MobileContractDownloadView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        contract = (
            ContractDocument.objects.filter(is_active=True)
            .order_by("-created_at", "-contract_id")
            .first()
        )
        if not contract or not contract.file:
            raise Http404("Active document was not found")
        filename = contract.file.name.split("/")[-1]
        return FileResponse(
            contract.file.open("rb"),
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )


@extend_schema(
    tags=["mobile_content"],
    parameters=[TermsQuerySerializer],
)
class MobileTermsConditionsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        params = TermsQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        text_type = params.validated_data["text_type"]
        obj = (
            TermsAndConditions.objects.filter(is_active=True, text_type=text_type)
            .order_by("-created_at", "-text_id")
            .first()
        )
        if not obj or not obj.text:
            raise Http404("Active document was not found")

        return Response(TermsAndConditionsSerializer(obj).data)


@extend_schema(
    tags=["mobile_content"]
)
class ContactsView(APIView):

    def get(self, request, *args, **kwargs):
        obj = Contacts.objects.order_by("-created_at", "-text_id").first()

        if not obj:
            raise Http404("Contacts not found!")

        return Response(ContactsSerializer(obj).data)

