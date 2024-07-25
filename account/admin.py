from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from account.models import User, File

class UserModelAdmin(BaseUserAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name', 'address', 'phone', 'age', 'is_admin', 'created_at')
    list_filter = ('is_admin',)
    fieldsets = (
        ('User Credentials', {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'address', 'phone', 'age')}),
        ('Permissions', {'fields': ('is_admin',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'address', 'phone', 'age', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('email', 'id')
    filter_horizontal = ()

admin.site.register(User, UserModelAdmin)
admin.site.register(File)
