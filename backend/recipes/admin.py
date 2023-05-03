from django.contrib import admin

from .models import (FavoriteRecipe, IngredientModel, RecipeIngredients,
                     RecipeModel, RecipeTag, ShoppingCartRecipes, TagModel)


class RecipeModelAdmin(admin.ModelAdmin):
    list_display = ('author', 'name', 'published',
                    'ingredients_list', 'tags_list', 'image',
                    'favoriting_count', 'id')
    search_fields = ('name',)
    list_filter = ('author', 'name', 'tags',)

    @admin.display(description='Список ингредиентов')
    def ingredients_list(self, obj):
        return [x.ingredients for x in
                obj.recipe_ingredients.all().prefetch_related('ingredients')
                .only('ingredients__name')]

    @admin.display(description='Список тегов')
    def tags_list(self, obj):
        return [x.name for x in obj.tags.all().prefetch_related('tags')]

    @admin.display(description='Добавлено в избранное, раз')
    def favoriting_count(self, obj):
        return obj.favoring_users.all().count()

# Работает, только если зайти на страницу рецепта в админке
# Не работает из под Admin Actions
    # def delete_model(self, request, obj):
    #     if obj.image is not None:
    #         obj.image.delete()
    #     return super().delete_model(request, obj)


class TagModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    search_fields = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'id')
    search_fields = ('name',)
    list_filter = ('name',)


class RecipeIngredientsAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredients', 'amount')


class RecipeTagsAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'tags')
    search_fields = ('recipe',)


class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


class ShoppingCartRecipesAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


admin.site.register(RecipeModel, RecipeModelAdmin)
admin.site.register(TagModel, TagModelAdmin)
admin.site.register(IngredientModel, IngredientAdmin)
admin.site.register(RecipeIngredients, RecipeIngredientsAdmin)
admin.site.register(RecipeTag, RecipeTagsAdmin)
admin.site.register(FavoriteRecipe, FavoriteRecipeAdmin)
admin.site.register(ShoppingCartRecipes, ShoppingCartRecipesAdmin)
