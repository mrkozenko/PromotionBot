from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import Post, Button, Chat, SubscribeLink


# Register your models here.
class ButtonInline(admin.TabularInline):
    model = Button
    extra = 1


class PostAdmin(admin.ModelAdmin):
    inlines = [ButtonInline]
    list_display = ["title", "chat_id"]

admin.site.register(Post, PostAdmin)

admin.site.register(Button)
admin.site.register(Chat)
admin.site.register(SubscribeLink)