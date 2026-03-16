# core/urls.py

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('academic-years/',                         views.academic_year_list,   name='academic_year_list'),
    path('academic-years/add/',                     views.academic_year_create, name='academic_year_create'),
    path('terms/',                                  views.term_list,            name='term_list'),
    path('terms/add/',                              views.term_create,          name='term_create'),
    path('terms/<int:pk>/edit/',                    views.term_edit,            name='term_edit'),
    path('terms/<int:pk>/generate-weeks/',          views.generate_weeks,       name='generate_weeks'),
    path('non-school-days/',                        views.non_school_day_list,  name='non_school_day_list'),
    path('non-school-days/add/',                    views.non_school_day_create,name='non_school_day_create'),
    path('non-school-days/<int:pk>/delete/',        views.non_school_day_delete,name='non_school_day_delete'),
    path('late-thresholds/',                        views.late_threshold_list,  name='late_threshold_list'),
    path('late-thresholds/add/',                    views.late_threshold_create,name='late_threshold_create'),
    path('late-thresholds/<int:pk>/edit/',          views.late_threshold_edit,  name='late_threshold_edit'),
    path('school-day-configs/',                     views.school_day_config_list,   name='school_day_config_list'),
    path('school-day-configs/add/',                 views.school_day_config_create, name='school_day_config_create'),
    path('school-day-configs/<int:pk>/delete/',     views.school_day_config_delete, name='school_day_config_delete'),
]