from backupdata.models import Channel, Message, ChannelMember
from django.contrib import admin

class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'channel',
        'user',
        'text'
    ]
    ordering = [
        '-ts'
    ]
    list_filter = [
        'channel',
        'user'
    ]

# Register your models here.
admin.site.register(Channel)
admin.site.register(Message, MessageAdmin)
admin.site.register(ChannelMember)
