from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField

from recipes.models import RecipeModel

from .models import Follow, User


class RecipesForSubscribesSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecipeModel
        fields = ('id', 'name', 'cooking_time')


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = SerializerMethodField('get_subscription')

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_subscription(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Follow.objects.filter(follower=self.context['request'].user,
                                     author=obj).exists()


class SubscribitionSerializer(serializers.ModelSerializer):
    is_subscribed = SerializerMethodField()
    recipes = SerializerMethodField()
    recipe_count = SerializerMethodField('get_recipe_count')

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipe_count')

    def get_is_subscribed(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Follow.objects.filter(follower=self.context['request'].user,
                                     author=obj).exists()

    def get_recipes(self, user):
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        print(recipes_limit)
        if not recipes_limit:
            recipes = user.recipes.all()
        else:
            recipes = user.recipes.all()[:int(recipes_limit)]
        if recipes:
            serializer = RecipesForSubscribesSerializer(recipes, many=True)
            return serializer.data
        return []

    def get_recipe_count(self, obj):
        return RecipeModel.objects.filter(author=obj).count()
