# devices/urls.py

from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    path('', views.device_list, name='device_list'),
    path('add/', views.device_create, name='device_create'),
    path('<int:pk>/edit/', views.device_edit, name='device_edit'),
    path('<int:pk>/delete/', views.device_delete, name='device_delete'),
    path('<int:pk>/sync/', views.device_sync, name='device_sync'),
    path('sync-all/', views.sync_all, name='sync_all'),
    path('punch-logs/', views.punch_log_list, name='punch_log_list'),
    path('<int:pk>/import-users/', views.import_users, name='import_users'),
    path('<int:pk>/map-user/', views.map_user, name='map_user'),
    path('<int:pk>/backup-fingerprints/', views.backup_fingerprints_view, name='backup_fingerprints'),
    path('<int:pk>/push-fingerprints/', views.push_fingerprints_view, name='push_fingerprints'),
    path('fingerprints/', views.fingerprint_list, name='fingerprint_list'),
]
