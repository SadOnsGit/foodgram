import django_filters

from food.models import Receipts


class ReceiptFilter(django_filters.FilterSet):
    author = django_filters.CharFilter(
        field_name="author__username", lookup_expr="icontains"
    )
    tag = django_filters.CharFilter(field_name="tag", lookup_expr="icontains")
    in_shopping_list = django_filters.CharFilter(
        method="filter_in_shopping_list"
    )
    in_favorites = django_filters.CharFilter(method="filter_in_favorites")

    def filter_in_shopping_list(self, queryset, name, value):
        if value == "1":
            user = self.request.user
            return user.purchased_receipts.all()
        return queryset

    def filter_in_favorites(self, queryset, name, value):
        if value == "1":
            user = self.request.user
            return user.favorited_receipts.all()
        return queryset

    class Meta:
        model = Receipts
        fields = ["author", "tag", "in_shopping_list", "in_favorites"]
