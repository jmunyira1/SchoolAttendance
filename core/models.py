from django.db import models
from django.core.exceptions import ValidationError


class AcademicYear(models.Model):
    year        = models.PositiveIntegerField(unique=True)  # e.g. 2025
    is_current  = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academic_years'
        ordering = ['-year']

    def __str__(self):
        return str(self.year)

    def save(self, *args, **kwargs):
        # only one academic year can be current at a time
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Term(models.Model):
    TERM_1 = 1
    TERM_2 = 2
    TERM_3 = 3

    TERM_CHOICES = [
        (TERM_1, 'Term 1'),
        (TERM_2, 'Term 2'),
        (TERM_3, 'Term 3'),
    ]

    academic_year   = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    term_number     = models.PositiveSmallIntegerField(choices=TERM_CHOICES)
    start_date      = models.DateField()
    end_date        = models.DateField()
    is_current      = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'terms'
        unique_together = ('academic_year', 'term_number')
        ordering = ['academic_year', 'term_number']

    def __str__(self):
        return f'{self.academic_year} - Term {self.term_number}'

    def clean(self):
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError('End date must be after start date.')

    def save(self, *args, **kwargs):
        # only one term can be current at a time
        if self.is_current:
            Term.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    @property
    def duration_weeks(self):
        delta = self.end_date - self.start_date
        return delta.days // 7


class SchoolWeek(models.Model):
    term        = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='weeks')
    week_number = models.PositiveSmallIntegerField()  # 1, 2, 3 ... within the term
    start_date  = models.DateField()
    end_date    = models.DateField()

    class Meta:
        db_table = 'school_weeks'
        unique_together = ('term', 'week_number')
        ordering = ['term', 'week_number']

    def __str__(self):
        return f'{self.term} - Week {self.week_number}'


class NonSchoolDay(models.Model):
    HOLIDAY     = 'holiday'
    CLOSURE     = 'closure'

    TYPE_CHOICES = [
        (HOLIDAY, 'Public Holiday'),
        (CLOSURE, 'Ad-hoc Closure'),
    ]

    date        = models.DateField(unique=True)
    name        = models.CharField(max_length=200)  # e.g. "Madaraka Day", "Staff Meeting"
    day_type    = models.CharField(max_length=20, choices=TYPE_CHOICES)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'non_school_days'
        ordering = ['date']

    def __str__(self):
        return f'{self.name} ({self.date})'


class SchoolDayConfig(models.Model):
    """
    Defines which days of the week are active school days.
    Can be configured per stream or applied school-wide (stream=None).
    Day numbers follow Python's weekday(): 0=Monday ... 6=Sunday
    """
    MONDAY      = 0
    TUESDAY     = 1
    WEDNESDAY   = 2
    THURSDAY    = 3
    FRIDAY      = 4
    SATURDAY    = 5
    SUNDAY      = 6

    DAY_CHOICES = [
        (MONDAY,    'Monday'),
        (TUESDAY,   'Tuesday'),
        (WEDNESDAY, 'Wednesday'),
        (THURSDAY,  'Thursday'),
        (FRIDAY,    'Friday'),
        (SATURDAY,  'Saturday'),
        (SUNDAY,    'Sunday'),
    ]

    # stream is set via ForeignKey in people app using a string reference
    # to avoid circular imports — see people/models.py
    stream      = models.ForeignKey(
                    'people.Stream',
                    on_delete=models.CASCADE,
                    related_name='day_configs',
                    null=True,
                    blank=True,
                    help_text='Leave blank to apply school-wide'
                  )
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)

    class Meta:
        db_table = 'school_day_configs'
        unique_together = ('stream', 'day_of_week')

    def __str__(self):
        stream_label = self.stream.name if self.stream else 'School-wide'
        return f'{stream_label} - {self.get_day_of_week_display()}'


class LateThreshold(models.Model):
    """
    Admin-configured cutoff time after which a check-in is considered late.
    Can be set per day type (weekday vs Saturday) or per specific stream.
    """
    WEEKDAY     = 'weekday'
    SATURDAY    = 'saturday'

    DAY_TYPE_CHOICES = [
        (WEEKDAY,   'Weekday'),
        (SATURDAY,  'Saturday'),
    ]

    day_type        = models.CharField(max_length=20, choices=DAY_TYPE_CHOICES)
    cutoff_time     = models.TimeField()  # e.g. 07:30
    applies_to      = models.ForeignKey(
                        'people.Stream',
                        on_delete=models.CASCADE,
                        related_name='late_thresholds',
                        null=True,
                        blank=True,
                        help_text='Leave blank to apply school-wide'
                      )
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'late_thresholds'
        unique_together = ('day_type', 'applies_to')

    def __str__(self):
        target = self.applies_to.name if self.applies_to else 'School-wide'
        return f'{self.get_day_type_display()} late after {self.cutoff_time} ({target})'