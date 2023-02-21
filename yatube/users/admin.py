from django.contrib import admin

from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'first_name', 'last_name', 'username', 'email', 'image')
    list_editable = ('username',)
    search_fields = ('first_name', 'last_name', 'username', 'email',)
    list_filter = ('first_name', 'last_name', 'username', 'email',)
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
