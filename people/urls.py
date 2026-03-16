# people/urls.py

from django.urls import path
from . import views
from .import_views import import_students

app_name = 'people'

urlpatterns = [
    # forms
    path('forms/', views.form_list, name='form_list'),
    path('forms/add/', views.form_create, name='form_create'),
    path('forms/<int:pk>/edit/', views.form_edit, name='form_edit'),

    # streams
    path('streams/', views.stream_list, name='stream_list'),
    path('streams/add/', views.stream_create, name='stream_create'),
    path('streams/<int:pk>/edit/', views.stream_edit, name='stream_edit'),

    # students
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('students/import/', import_students, name='import_students'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),

    # staff
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_create, name='staff_create'),
    path('staff/<int:pk>/', views.staff_detail, name='staff_detail'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/delete/', views.staff_delete, name='staff_delete'),
]