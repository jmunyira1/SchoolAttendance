from django.contrib import admin
from .models import AcademicYear, Term, SchoolWeek, NonSchoolDay, SchoolDayConfig, LateThreshold


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'is_current', 'created_at')
    list_filter  = ('is_current',)


class SchoolWeekInline(admin.TabularInline):
    model  = SchoolWeek
    extra  = 0
    fields = ('week_number', 'start_date', 'end_date')


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'start_date', 'end_date', 'is_current', 'duration_weeks')
    list_filter  = ('academic_year', 'is_current')
    inlines      = [SchoolWeekInline]


@admin.register(NonSchoolDay)
class NonSchoolDayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'day_type')
    list_filter  = ('day_type',)
    ordering     = ('date',)


@admin.register(SchoolDayConfig)
class SchoolDayConfigAdmin(admin.ModelAdmin):
    list_display = ('stream', 'get_day_of_week_display')
    list_filter  = ('day_of_week',)


@admin.register(LateThreshold)
class LateThresholdAdmin(admin.ModelAdmin):
    list_display = ('day_type', 'cutoff_time', 'applies_to')
    list_filter  = ('day_type',)