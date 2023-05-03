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
    is_subscribed = SerializerMethodField('get_subscription')
    recipes = RecipesForSubscribesSerializer(many=True, read_only=True)
    recipe_count = SerializerMethodField('get_recipe_count')

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipe_count')

    def get_subscription(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Follow.objects.filter(follower=self.context['request'].user,
                                     author=obj).exists()

    def get_recipe_count(self, obj):
        return RecipeModel.objects.filter(author=obj).count()

    def to_representation(self, instance):
        recipes_limit = int(self.context['request'].GET.get('recipes_limit'))
        if not recipes_limit:  # Какое поведение необходимо при 0?
            return super().to_representation(instance)
        representation = super().to_representation(instance)
        representation['recipes'] = representation['recipes'][:recipes_limit]
        return representation
