# attendance/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from datetime import date, timedelta

from .models import AttendanceRecord, AttendanceOverrideLog
from people.models import Student, StaffMember, Stream
from core.models import Term, AcademicYear, SchoolWeek
from accounts.decorators import admin_or_principal_required, storekeeper_required


def get_current_term():
    return Term.objects.filter(is_current=True).select_related('academic_year').first()


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
@admin_or_principal_required
def attendance_dashboard(request):
    today        = date.today()
    current_term = get_current_term()

    present_students = AttendanceRecord.objects.filter(
        date=today, person_type=AttendanceRecord.STUDENT,
        status__in=[AttendanceRecord.PRESENT, AttendanceRecord.LATE]
    ).count()

    absent_students = AttendanceRecord.objects.filter(
        date=today, person_type=AttendanceRecord.STUDENT,
        status=AttendanceRecord.ABSENT
    ).count()

    late_students = AttendanceRecord.objects.filter(
        date=today, person_type=AttendanceRecord.STUDENT,
        status=AttendanceRecord.LATE
    ).count()

    present_staff = AttendanceRecord.objects.filter(
        date=today, person_type=AttendanceRecord.STAFF,
        status__in=[AttendanceRecord.PRESENT, AttendanceRecord.LATE]
    ).count()

    late_staff = AttendanceRecord.objects.filter(
        date=today, person_type=AttendanceRecord.STAFF,
        status=AttendanceRecord.LATE
    ).count()

    total_students = Student.objects.filter(is_active=True).count()
    total_staff    = StaffMember.objects.filter(is_active=True).count()

    context = {
        'today'           : today,
        'current_term'    : current_term,
        'present_students': present_students,
        'absent_students' : absent_students,
        'late_students'   : late_students,
        'present_staff'   : present_staff,
        'late_staff'      : late_staff,
        'total_students'  : total_students,
        'total_staff'     : total_staff,
    }
    return render(request, 'attendance/dashboard.html', context)


# ─── Student attendance ────────────────────────────────────────────────────────

@login_required
@admin_or_principal_required
def daily_attendance(request):


    selected_date   = request.GET.get('date', date.today().isoformat())
    selected_stream = request.GET.get('stream', '')
    selected_type   = request.GET.get('type', 'student')

    try:
        selected_date = date.fromisoformat(selected_date)
    except ValueError:
        selected_date = date.today()

    records = AttendanceRecord.objects.filter(
        date=selected_date, person_type=selected_type,
    ).select_related('student', 'student__stream', 'student__stream__form', 'staff_member')

    if selected_stream and selected_type == 'student':
        records = records.filter(student__stream_id=selected_stream)

    streams = Stream.objects.all().select_related('form')

    context = {
        'records'        : records,
        'selected_date'  : selected_date,
        'selected_stream': selected_stream,
        'selected_type'  : selected_type,
        'streams'        : streams,
    }
    return render(request, 'attendance/daily.html', context)


@login_required
@admin_or_principal_required
def student_attendance(request, pk):
    student      = get_object_or_404(Student, pk=pk)
    current_term = get_current_term()

    records = AttendanceRecord.objects.filter(
        student=student, term=current_term
    ).order_by('-date') if current_term else []

    context = {
        'student'     : student,
        'records'     : records,
        'current_term': current_term,
    }
    return render(request, 'attendance/student_detail.html', context)


@login_required
@admin_or_principal_required
def override_attendance(request, pk):
    record = get_object_or_404(AttendanceRecord, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        note       = request.POST.get('note', '')

        if new_status in dict(AttendanceRecord.STATUS_CHOICES):
            AttendanceOverrideLog.objects.create(
                attendance_record=record,
                changed_by=request.user,
                previous_status=record.status,
                new_status=new_status,
                note=note,
            )
            record.status        = new_status
            record.is_overridden = True
            record.overridden_by = request.user
            record.override_note = note
            record.overridden_at = timezone.now()
            record.save()
            messages.success(request, 'Attendance record updated.')
        else:
            messages.error(request, 'Invalid status.')

        return redirect(request.POST.get('next', 'attendance:daily'))

    context = {
        'record'  : record,
        'statuses': AttendanceRecord.STATUS_CHOICES,
    }
    return render(request, 'attendance/override.html', context)


@login_required
@admin_or_principal_required
def absentee_report(request):

    selected_date   = request.GET.get('date', date.today().isoformat())
    selected_stream = request.GET.get('stream', '')

    try:
        selected_date = date.fromisoformat(selected_date)
    except ValueError:
        selected_date = date.today()

    absentees = AttendanceRecord.objects.filter(
        date=selected_date, person_type=AttendanceRecord.STUDENT,
        status=AttendanceRecord.ABSENT,
    ).select_related('student', 'student__stream', 'student__stream__form')

    if selected_stream:
        absentees = absentees.filter(student__stream_id=selected_stream)

    streams = Stream.objects.all().select_related('form')

    context = {
        'absentees'      : absentees,
        'selected_date'  : selected_date,
        'selected_stream': selected_stream,
        'streams'        : streams,
    }
    return render(request, 'attendance/absentees.html', context)


@login_required
@admin_or_principal_required
def term_summary(request):
    current_term    = get_current_term()
    selected_stream = request.GET.get('stream', '')
    streams         = Stream.objects.all().select_related('form')

    summary = []
    if current_term:
        students = Student.objects.filter(is_active=True).select_related('stream', 'stream__form')
        if selected_stream:
            students = students.filter(stream_id=selected_stream)

        for student in students:
            records = AttendanceRecord.objects.filter(student=student, term=current_term)
            total   = records.count()
            present = records.filter(status=AttendanceRecord.PRESENT).count()
            late    = records.filter(status=AttendanceRecord.LATE).count()
            summary.append({
                'student': student,
                'present': present,
                'late'   : late,
                'absent' : records.filter(status=AttendanceRecord.ABSENT).count(),
                'excused': records.filter(status=AttendanceRecord.EXCUSED).count(),
                'total'  : total,
                'pct'    : round((present + late) / total * 100) if total else 0,
            })

    context = {
        'summary'        : summary,
        'current_term'   : current_term,
        'streams'        : streams,
        'selected_stream': selected_stream,
    }
    return render(request, 'attendance/term_summary.html', context)


# ─── Staff attendance ──────────────────────────────────────────────────────────

@login_required
@admin_or_principal_required
def staff_daily(request):
    """Daily staff register — who is present/absent/late today."""

    selected_date = request.GET.get('date', date.today().isoformat())
    selected_type = request.GET.get('staff_type', '')  # teaching / non_teaching

    try:
        selected_date = date.fromisoformat(selected_date)
    except ValueError:
        selected_date = date.today()

    records = AttendanceRecord.objects.filter(
        date=selected_date,
        person_type=AttendanceRecord.STAFF,
    ).select_related('staff_member').order_by(
        'staff_member__staff_type', 'staff_member__full_name'
    )

    if selected_type:
        records = records.filter(staff_member__staff_type=selected_type)

    # staff with no punch today — absent but no record yet
    enrolled_staff = StaffMember.objects.filter(
        is_active=True, zk_user_id__isnull=False
    )
    if selected_type:
        enrolled_staff = enrolled_staff.filter(staff_type=selected_type)

    recorded_ids = records.values_list('staff_member_id', flat=True)
    unrecorded   = enrolled_staff.exclude(pk__in=recorded_ids)

    context = {
        'records'      : records,
        'unrecorded'   : unrecorded,
        'selected_date': selected_date,
        'selected_type': selected_type,
        'present_count': records.filter(status__in=[AttendanceRecord.PRESENT, AttendanceRecord.LATE]).count(),
        'absent_count' : records.filter(status=AttendanceRecord.ABSENT).count() + unrecorded.count(),
        'late_count'   : records.filter(status=AttendanceRecord.LATE).count(),
        'total_count'  : enrolled_staff.count(),
    }
    return render(request, 'attendance/staff_daily.html', context)


@login_required
@admin_or_principal_required
def staff_term_summary(request):
    """Term summary — days present/absent/late per staff member."""
    current_term  = get_current_term()
    selected_type = request.GET.get('staff_type', '')

    summary = []
    if current_term:
        staff = StaffMember.objects.filter(is_active=True).order_by('staff_type', 'full_name')
        if selected_type:
            staff = staff.filter(staff_type=selected_type)

        for member in staff:
            records = AttendanceRecord.objects.filter(
                staff_member=member, term=current_term
            )
            total   = records.count()
            present = records.filter(status=AttendanceRecord.PRESENT).count()
            late    = records.filter(status=AttendanceRecord.LATE).count()
            absent  = records.filter(status=AttendanceRecord.ABSENT).count()
            excused = records.filter(status=AttendanceRecord.EXCUSED).count()
            summary.append({
                'member' : member,
                'present': present,
                'late'   : late,
                'absent' : absent,
                'excused': excused,
                'total'  : total,
                'pct'    : round((present + late) / total * 100) if total else 0,
            })

    context = {
        'summary'      : summary,
        'current_term' : current_term,
        'selected_type': selected_type,
    }
    return render(request, 'attendance/staff_term_summary.html', context)


@login_required
@admin_or_principal_required
def staff_late_arrivals(request):
    """Late arrivals report — staff who checked in late, filterable by date range."""

    # default to current week
    today      = date.today()
    week_start = today - timedelta(days=today.weekday())
    date_from  = request.GET.get('date_from', week_start.isoformat())
    date_to    = request.GET.get('date_to', today.isoformat())
    selected_type = request.GET.get('staff_type', '')

    try:
        date_from = date.fromisoformat(date_from)
        date_to   = date.fromisoformat(date_to)
    except ValueError:
        date_from = week_start
        date_to   = today

    late_records = AttendanceRecord.objects.filter(
        person_type=AttendanceRecord.STAFF,
        status=AttendanceRecord.LATE,
        date__gte=date_from,
        date__lte=date_to,
    ).select_related('staff_member').order_by('-date', 'check_in')

    if selected_type:
        late_records = late_records.filter(staff_member__staff_type=selected_type)

    # summary — most late arrivals by staff member
    by_member = {}
    for record in late_records:
        m = record.staff_member
        if m.pk not in by_member:
            by_member[m.pk] = {'member': m, 'count': 0, 'dates': []}
        by_member[m.pk]['count'] += 1
        by_member[m.pk]['dates'].append(record.date)

    sorted_summary = sorted(by_member.values(), key=lambda x: x['count'], reverse=True)

    context = {
        'late_records'  : late_records,
        'summary'       : sorted_summary,
        'date_from'     : date_from,
        'date_to'       : date_to,
        'selected_type' : selected_type,
        'total_late'    : late_records.count(),
    }
    return render(request, 'attendance/staff_late_arrivals.html', context)


@login_required
@admin_or_principal_required
def staff_attendance(request, pk):
    """Individual staff member attendance history for current term."""
    staff_member = get_object_or_404(StaffMember, pk=pk)
    current_term = get_current_term()

    records = AttendanceRecord.objects.filter(
        staff_member=staff_member, term=current_term
    ).order_by('-date') if current_term else []

    total   = records.count() if current_term else 0
    present = records.filter(status=AttendanceRecord.PRESENT).count() if current_term else 0
    late    = records.filter(status=AttendanceRecord.LATE).count() if current_term else 0
    absent  = records.filter(status=AttendanceRecord.ABSENT).count() if current_term else 0

    context = {
        'staff_member': staff_member,
        'records'     : records,
        'current_term': current_term,
        'total'       : total,
        'present'     : present,
        'late'        : late,
        'absent'      : absent,
        'pct'         : round((present + late) / total * 100) if total else 0,
    }
    return render(request, 'attendance/staff_detail.html', context)


# ─── Storekeeper ──────────────────────────────────────────────────────────────

@login_required
@storekeeper_required
def storekeeper_view(request):
    today   = date.today()
    streams = Stream.objects.all().select_related('form').order_by('form__order', 'name')

    headcounts = []
    for stream in streams:
        present = AttendanceRecord.objects.filter(
            date=today, person_type=AttendanceRecord.STUDENT,
            student__stream=stream,
            status__in=[AttendanceRecord.PRESENT, AttendanceRecord.LATE],
        ).count()
        total = Student.objects.filter(stream=stream, is_active=True).count()
        headcounts.append({
            'stream' : stream,
            'present': present,
            'total'  : total,
            'absent' : total - present,
        })

    staff_present = AttendanceRecord.objects.filter(
        date=today, person_type=AttendanceRecord.STAFF,
        status__in=[AttendanceRecord.PRESENT, AttendanceRecord.LATE],
    ).count()
    total_staff = StaffMember.objects.filter(is_active=True).count()

    context = {
        'today'        : today,
        'headcounts'   : headcounts,
        'staff_present': staff_present,
        'total_staff'  : total_staff,
    }
    return render(request, 'attendance/storekeeper.html', context)