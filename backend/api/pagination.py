from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class UserPageNumberPagination(PageNumberPagination):
    page_size = settings.PAGE_SIZE
    page_size_query_param = "limit"
    max_page_size = settings.MAX_PAGE_SIZE
