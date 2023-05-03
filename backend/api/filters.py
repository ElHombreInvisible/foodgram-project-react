from django_filters import CharFilter, Filter, FilterSet, NumberFilter

from recipes.models import IngredientModel, RecipeModel


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = IngredientModel
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = Filter(method='tag_filter')
    author = NumberFilter(field_name='author_id', lookup_expr='exact')
    is_favorited = Filter(method='get_favorite')
    is_in_shopping_cart = Filter(method='get_shopping_cart')

    class Meta:
        model = RecipeModel
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_favorite(self, queryset, field, value):
        if value == '0':
            return queryset
        return queryset.filter(favoring_users__user=self.request.user)

    def get_shopping_cart(self, queryset, field, value):
        if value == '0':
            return queryset
        return queryset.filter(
            recipes_in_shopping_card__user=self.request.user)

    def tag_filter(self, queryset, field_name, value):
        tags = self.data.getlist('tags')
        if tags is None:
            return queryset
        return queryset.filter(tags__slug__in=tags)
