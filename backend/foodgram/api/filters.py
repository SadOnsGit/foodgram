from django_filters import FilterSet, CharFilter

from food.models import Recipe, Ingredients


class RecipeFilter(FilterSet):
    author = CharFilter(
        field_name="author__username", lookup_expr="icontains"
    )
    tag = CharFilter(field_name="tag", lookup_expr="icontains")
    in_shopping_list = CharFilter(method="filter_in_shopping_list")
    in_favorites = CharFilter(method="filter_in_favorites")

    def filter_in_shopping_list(self, queryset, name, value):
        if value == "1":
            user = self.request.user
            return user.purchases.all()
        return queryset

    def filter_in_favorites(self, queryset, name, value):
        if value == "1":
            user = self.request.user
            return user.favorite_recipe.all()
        return queryset

    class Meta:
        model = Recipe
        fields = ["author", "tag", "in_shopping_list", "in_favorites"]


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Ingredients
        fields = ['name']
