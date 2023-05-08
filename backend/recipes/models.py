from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from users.models import User


class TagModel(models.Model):
    name = models.CharField(unique=True, max_length=200)
    color = models.CharField(
        unique=True,
        max_length=7,
        validators=[RegexValidator(r'#[A-Fa-f0-9]{6}'), ]
        )
    slug = models.SlugField(
        unique=True,
        max_length=200,
        validators=[RegexValidator(r'^[-a-zA-Z0-9_]+$'), ]
        )

    def __str__(self) -> str:
        return self.name[:30]


class IngredientModel(models.Model):
    name = models.CharField(max_length=80,
                            unique=True,
                            db_index=True)
    measurement_unit = models.CharField(max_length=30)

    def __str__(self) -> str:
        return self.name[:30]


class RecipeModel(models.Model):
    author = models.ForeignKey(User, on_delete=models.PROTECT,
                               verbose_name='Автор',
                               related_name='recipes')
    ingredients = models.ManyToManyField(IngredientModel,
                                         through='RecipeIngredients',
                                         verbose_name='Ингредиенты')
    tags = models.ManyToManyField(TagModel,
                                  related_name='recipes',
                                  )
    name = models.CharField(max_length=200, blank=False,
                            verbose_name='Название рецепта')
    text = models.TextField(blank=False)
    image = models.ImageField(upload_to='images/',
                              verbose_name='Изображение')
    cooking_time = models.PositiveIntegerField(
        blank=False,
        validators=[MinValueValidator(1),
                    MaxValueValidator(4320)])
    published = models.DateTimeField(auto_now_add=True,
                                     verbose_name='Дата публикации')

    def __str__(self) -> str:
        return self.name[:30]

    class Meta:
        ordering = ['-published']


# предпочтительный способ удаления изображения через сигналы
# или переопределение в админке
@receiver(pre_delete, sender=RecipeModel)
def delete_image_hook(sender, instance, using, **kwargs):
    if instance.image is not None:
        instance.image.delete()


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        RecipeModel,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE
        )
    ingredients = models.ForeignKey(
        IngredientModel,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipes'
        )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1),
                    MaxValueValidator(10000)]
        )

    class Meta:
        constraints = [
          UniqueConstraint(fields=['recipe', 'ingredients'],
                           name='unique_ingredient'),
        ]

    def __str__(self) -> str:
        return f'{self.ingredients} в "{self.recipe}"'


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(User, related_name='favorite_recipes',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(RecipeModel, related_name='favoring_users',
                               on_delete=models.CASCADE)

    class Meta:
        constraints = [
          UniqueConstraint(fields=['recipe', 'user'],
                           name='unique_favorite'),
        ]


class ShoppingCartRecipes(models.Model):
    user = models.ForeignKey(User, related_name='in_user_cards',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(RecipeModel,
                               related_name='recipes_in_shopping_card',
                               on_delete=models.CASCADE)

    class Meta:
        constraints = [
          UniqueConstraint(fields=['recipe', 'user'],
                           name='unique_shopping_cart'),
        ]
