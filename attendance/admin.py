from django.contrib import admin
from .models import AttendanceRecord, AttendanceOverrideLog


class AttendanceOverrideLogInline(admin.TabularInline):
    model           = AttendanceOverrideLog
    extra           = 0
    readonly_fields = ('changed_by', 'previous_status', 'new_status', 'note', 'changed_at')
    can_delete      = False


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display    = ('__str__', 'date', 'status', 'check_in', 'check_out', 'is_overridden')
    list_filter     = ('status', 'person_type', 'term', 'is_overridden')
    search_fields   = ('student__full_name', 'student__admission_number',
                       'staff_member__full_name', 'staff_member__staff_id')
    ordering        = ('-date',)
    readonly_fields = ('created_at', 'updated_at')
    inlines         = [AttendanceOverrideLogInline]


@admin.register(AttendanceOverrideLog)
class AttendanceOverrideLogAdmin(admin.ModelAdmin):
    list_display    = ('attendance_record', 'changed_by', 'previous_status', 'new_status', 'changed_at')
    readonly_fields = ('attendance_record', 'changed_by', 'previous_status', 'new_status', 'note', 'changed_at')
    ordering        = ('-changed_at',)