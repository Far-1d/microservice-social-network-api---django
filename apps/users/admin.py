from django.contrib import admin
from .models import User

# Register your models here.
class AdminUser(admin.ModelAdmin):
    pass

admin.site.register(User, AdminUser)
