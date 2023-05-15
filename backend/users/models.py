from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q
from django.db.models.constraints import CheckConstraint, UniqueConstraint


class User(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        constraints = [
            CheckConstraint(
                check=~Q(username__iexact="me"),
                name="'me' username constraint"
            ),
            CheckConstraint(
                check=~Q(username__iexact="set_password"),
                name="'set_password' username constraint"
            )
        ]
        ordering = ['-pk']

    def __str__(self) -> str:
        return self.username


class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='follows',
                                 on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='followed_by')

    class Meta:
        constraints = [
            UniqueConstraint(fields=['follower', 'author'],
                             name='unique_following'),
            CheckConstraint(check=~Q(author=F('follower')),
                            name='self following constraint')
        ]

    def __str__(self) -> str:
        return f'{self.follower} подписан на "{self.author}"'
