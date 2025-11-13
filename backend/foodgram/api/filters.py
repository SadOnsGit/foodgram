from django_filters import (CharFilter, FilterSet, MultipleChoiceFilter,
                            NumberFilter)

from food.models import Ingredients, Recipe, Tags


class RecipeFilter(FilterSet):
    author = NumberFilter(field_name="author__pk")
    tags = MultipleChoiceFilter(
        field_name="tags__slug",
        choices=[(tag.slug, tag.slug) for tag in Tags.objects.all()],
    )
    is_favorited = CharFilter(method="filter_is_favorited")
    is_in_shopping_cart = CharFilter(method="filter_is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated or value != "1":
            return queryset
        return queryset.filter(in_favorites=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated or value != "1":
            return queryset
        return queryset.filter(in_shopping_list=user)

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr="icontains")

    class Meta:
        model = Ingredients
        fields = ["name"]
