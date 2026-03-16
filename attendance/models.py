from django.db import models
from django.conf import settings


class AttendanceRecord(models.Model):
    """
    One record per person per school day.
    Created/updated by processing PunchLogs.
    check_in  = first punch of the day
    check_out = last punch of the day
    """
    PRESENT = 'present'
    ABSENT  = 'absent'
    LATE    = 'late'
    EXCUSED = 'excused'

    STATUS_CHOICES = [
        (PRESENT,   'Present'),
        (ABSENT,    'Absent'),
        (LATE,      'Late'),
        (EXCUSED,   'Excused'),
    ]

    STUDENT = 'student'
    STAFF   = 'staff'

    PERSON_TYPE_CHOICES = [
        (STUDENT,   'Student'),
        (STAFF,     'Staff'),
    ]

    # who
    person_type     = models.CharField(max_length=10, choices=PERSON_TYPE_CHOICES)
    student         = models.ForeignKey(
                        'people.Student',
                        on_delete=models.CASCADE,
                        related_name='attendance_records',
                        null=True, blank=True
                      )
    staff_member    = models.ForeignKey(
                        'people.StaffMember',
                        on_delete=models.CASCADE,
                        related_name='attendance_records',
                        null=True, blank=True
                      )

    # when
    date            = models.DateField()
    academic_year   = models.ForeignKey('core.AcademicYear', on_delete=models.PROTECT, related_name='attendance_records')
    term            = models.ForeignKey('core.Term', on_delete=models.PROTECT, related_name='attendance_records')
    school_week     = models.ForeignKey(
                        'core.SchoolWeek',
                        on_delete=models.PROTECT,
                        related_name='attendance_records',
                        null=True, blank=True
                      )

    # punch data
    check_in        = models.TimeField(null=True, blank=True)
    check_out       = models.TimeField(null=True, blank=True)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ABSENT)

    # override tracking
    is_overridden   = models.BooleanField(default=False)
    overridden_by   = models.ForeignKey(
                        settings.AUTH_USER_MODEL,
                        on_delete=models.SET_NULL,
                        null=True, blank=True,
                        related_name='attendance_overrides'
                      )
    override_note   = models.CharField(max_length=255, blank=True)
    overridden_at   = models.DateTimeField(null=True, blank=True)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_records'
        # one record per person per day
        unique_together = [
            ('student', 'date'),
            ('staff_member', 'date'),
        ]
        ordering = ['-date', 'person_type']
        indexes = [
            models.Index(fields=['date', 'person_type']),
            models.Index(fields=['term', 'status']),
            models.Index(fields=['school_week']),
        ]

    def __str__(self):
        person = self.student or self.staff_member
        return f'{person} - {self.date} - {self.get_status_display()}'

    def clean(self):
        from django.core.exceptions import ValidationError
        # ensure only one of student or staff_member is set
        if self.student and self.staff_member:
            raise ValidationError('A record cannot belong to both a student and a staff member.')
        if not self.student and not self.staff_member:
            raise ValidationError('A record must belong to either a student or a staff member.')


class AttendanceOverrideLog(models.Model):
    """
    Audit trail — every change to an AttendanceRecord is logged here.
    """
    attendance_record   = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE, related_name='override_logs')
    changed_by          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    previous_status     = models.CharField(max_length=10)
    new_status          = models.CharField(max_length=10)
    note                = models.CharField(max_length=255, blank=True)
    changed_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance_override_logs'
        ordering = ['-changed_at']

    def __str__(self):
        return f'{self.attendance_record} changed to {self.new_status} by {self.changed_by}'