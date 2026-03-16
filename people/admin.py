from django.contrib import admin
from .models import Form, Stream, Student, StaffMember


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering     = ('order',)


class StreamInline(admin.TabularInline):
    model  = Stream
    extra  = 0
    fields = ('name',)


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display  = ('full_name', 'form')
    list_filter   = ('form',)
    search_fields = ('name', 'form__name')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ('admission_number', 'full_name', 'stream', 'is_active', 'zk_user_id')
    list_filter   = ('stream__form', 'stream', 'is_active', 'gender')
    search_fields = ('admission_number', 'full_name')
    ordering      = ('stream', 'full_name')


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display  = ('staff_id', 'full_name', 'staff_type', 'designation', 'is_active', 'zk_user_id')
    list_filter   = ('staff_type', 'is_active')
    search_fields = ('staff_id', 'full_name', 'designation')