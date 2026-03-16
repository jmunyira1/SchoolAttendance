from django.contrib import admin
from .models import Device, PunchLog


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display  = ('name', 'ip_address', 'port', 'location', 'is_active', 'last_sync')
    list_filter   = ('is_active',)
    search_fields = ('name', 'ip_address', 'location')


@admin.register(PunchLog)
class PunchLogAdmin(admin.ModelAdmin):
    list_display  = ('zk_user_id', 'person_type', 'device', 'punch_time', 'is_processed')
    list_filter   = ('person_type', 'is_processed', 'device')
    search_fields = ('zk_user_id',)
    ordering      = ('-punch_time',)
    readonly_fields = ('created_at',)