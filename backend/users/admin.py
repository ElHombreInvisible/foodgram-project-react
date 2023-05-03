from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Follow, User


class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'author')
    search_fields = ('following',)


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)
