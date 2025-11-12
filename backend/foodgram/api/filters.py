from django_filters import FilterSet, CharFilter, NumberFilter, MultipleChoiceFilter

from food.models import Recipe, Ingredients, Tags


class RecipeFilter(FilterSet):
    author = NumberFilter(field_name="author__pk")
    tags = MultipleChoiceFilter(
        field_name="tags__slug",
        choices=[(tag.slug, tag.slug) for tag in Tags.objects.all()]
    )
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
        fields = ["author", "tags", "in_shopping_list", "in_favorites"]


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Ingredients
        fields = ['name']
