# attendance/urls.py

from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # dashboard
    path('',                                views.attendance_dashboard,     name='dashboard'),

    # student attendance
    path('daily/',                          views.daily_attendance,         name='daily'),
    path('student/<int:pk>/',               views.student_attendance,       name='student_detail'),
    path('override/<int:pk>/',              views.override_attendance,      name='override'),
    path('absentees/',                      views.absentee_report,          name='absentees'),
    path('term-summary/',                   views.term_summary,             name='term_summary'),

    # staff attendance
    path('staff/daily/',                    views.staff_daily,              name='staff_daily'),
    path('staff/term-summary/',             views.staff_term_summary,       name='staff_term_summary'),
    path('staff/late-arrivals/',            views.staff_late_arrivals,      name='staff_late_arrivals'),
    path('staff/<int:pk>/',                 views.staff_attendance,         name='staff_detail'),

    # storekeeper
    path('storekeeper/',                    views.storekeeper_view,         name='storekeeper'),
]