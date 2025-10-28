from rest_framework.pagination import PageNumberPagination

from core.constants import MAX_PAGE_SIZE


class LimitPagination(PageNumberPagination):
    """Пагинация page/limit с верхним порогом размера страницы."""

    page_query_param = 'page'
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE
