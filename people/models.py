from django.db import models


class Form(models.Model):
    """
    Represents a form/grade level e.g. Form 3, Form 4, Grade 10
    """
    name        = models.CharField(max_length=50, unique=True)  # e.g. "Form 3", "Grade 10"
    order       = models.PositiveSmallIntegerField(default=0)   # for sorting
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'forms'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Stream(models.Model):
    """
    A stream is a class within a form e.g. Form 3 East, Form 4 West
    """
    form        = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='streams')
    name        = models.CharField(max_length=50)   # e.g. "East", "West", "North"
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'streams'
        unique_together = ('form', 'name')
        ordering = ['form', 'name']

    def __str__(self):
        return f'{self.form} {self.name}'

    @property
    def full_name(self):
        return f'{self.form} {self.name}'


class Student(models.Model):
    admission_number    = models.CharField(max_length=20, unique=True)
    full_name           = models.CharField(max_length=255)
    stream              = models.ForeignKey(Stream, on_delete=models.PROTECT, related_name='students')
    date_of_birth       = models.DateField(null=True, blank=True)
    gender              = models.CharField(
                            max_length=10,
                            choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
                            blank=True
                          )
    photo               = models.ImageField(upload_to='students/', null=True, blank=True)
    zk_user_id          = models.PositiveIntegerField(
                            unique=True,
                            null=True,
                            blank=True,
                            help_text='User ID enrolled on the ZKTeco device'
                          )
    is_active           = models.BooleanField(default=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        ordering = ['stream', 'full_name']

    def __str__(self):
        return f'{self.full_name} ({self.admission_number})'


class StaffMember(models.Model):
    TEACHING        = 'teaching'
    NON_TEACHING    = 'non_teaching'

    STAFF_TYPE_CHOICES = [
        (TEACHING,      'Teaching Staff'),
        (NON_TEACHING,  'Non-teaching Staff'),
    ]

    # identifier — TSC number for teachers, National ID for non-teaching
    staff_id        = models.CharField(
                        max_length=30,
                        unique=True,
                        help_text='TSC number for teachers, National ID for non-teaching staff'
                      )
    full_name       = models.CharField(max_length=255)
    staff_type      = models.CharField(max_length=20, choices=STAFF_TYPE_CHOICES)
    designation     = models.CharField(max_length=100, blank=True)  # e.g. "Mathematics Teacher", "Storekeeper"
    photo           = models.ImageField(upload_to='staff/', null=True, blank=True)
    zk_user_id      = models.PositiveIntegerField(
                        unique=True,
                        null=True,
                        blank=True,
                        help_text='User ID enrolled on the ZKTeco device'
                      )
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff_members'
        ordering = ['staff_type', 'full_name']

    def __str__(self):
        return f'{self.full_name} ({self.staff_id})'

    @property
    def id_label(self):
        return 'TSC No.' if self.staff_type == self.TEACHING else 'National ID'