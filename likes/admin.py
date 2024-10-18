from django.contrib import admin

# Register your models here.
from .models import LikedItem

@admin.register(LikedItem)
class LikedItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_object']