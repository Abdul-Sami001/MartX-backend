from django.contrib import admin
from .models import Tag, TaggedItem

# Register your models here.


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ['label']
    list_display = ['label']


@admin.register(TaggedItem)
class TaggedItemAdmin(admin.ModelAdmin):
    list_display = ['tag', 'content_object']