from django.core.paginator import InvalidPage
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination


class EmptyList(APIException):
    status_code = status.HTTP_200_OK
    default_detail = 'Not found.'
    default_code = 'not_found'


class BasePagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100
    page_size_query_param = 'page_size'
    page_query_param = 'page'
    page_query_description = 'IMPORTANT! To get data with no pagination do not provide "page" parameter,' \
                             ' starting from page=1 will return results with pagination'

    def paginate_queryset(self, queryset, request, view=None):

        page_size = self.get_page_size(request)
        if not page_size:
            return None

        if 'page' not in request.query_params:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)

        try:
            self.page = paginator.page(page_number)

        except InvalidPage as exc:
            msg = []
            raise EmptyList(msg)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return list(self.page)
