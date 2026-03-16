from django.db import models


class Device(models.Model):
    name        = models.CharField(max_length=100)          # e.g. "Main Gate", "Staff Entrance"
    ip_address  = models.GenericIPAddressField(unique=True)
    port        = models.PositiveIntegerField(default=4370) # ZKTeco default port
    location    = models.CharField(max_length=200, blank=True)
    is_active   = models.BooleanField(default=True)
    last_sync   = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devices'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.ip_address})'


class FingerprintTemplate(models.Model):
    """
    Stores a fingerprint template pulled from a ZKTeco device.
    Each person can have up to 10 fingers (finger_id 0-9).
    Templates are stored as binary blobs in ZKTeco's proprietary format
    and can be pushed back to any K40 Pro device.
    """
    zk_user_id  = models.PositiveIntegerField(help_text='ZK device user ID')
    finger_id   = models.PositiveSmallIntegerField(
                    help_text='Finger index 0-9 (0=right thumb, 1=right index, etc.)'
                  )
    template    = models.BinaryField(help_text='Raw ZKTeco fingerprint template binary data')
    quality     = models.PositiveSmallIntegerField(default=0, help_text='Template quality score')
    backed_up_from = models.ForeignKey(
                    Device,
                    on_delete=models.SET_NULL,
                    null=True, blank=True,
                    related_name='fingerprint_backups',
                    help_text='Device this template was pulled from'
                  )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'fingerprint_templates'
        unique_together = ('zk_user_id', 'finger_id')
        ordering        = ['zk_user_id', 'finger_id']

    def __str__(self):
        return f'ZK#{self.zk_user_id} finger {self.finger_id}'


class PunchLog(models.Model):
    """
    Raw punch record pulled directly from the ZKTeco device.
    One row per punch event. The attendance app processes these
    into daily AttendanceRecords.
    """
    STUDENT = 'student'
    STAFF   = 'staff'

    PERSON_TYPE_CHOICES = [
        (STUDENT,   'Student'),
        (STAFF,     'Staff'),
    ]

    device          = models.ForeignKey(Device, on_delete=models.PROTECT, related_name='punch_logs')
    zk_user_id      = models.PositiveIntegerField(help_text='User ID as stored on the ZKTeco device')
    person_type     = models.CharField(max_length=10, choices=PERSON_TYPE_CHOICES, blank=True)
    punch_time      = models.DateTimeField()
    is_processed    = models.BooleanField(default=False, help_text='True once converted to an AttendanceRecord')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'punch_logs'
        # prevent duplicate punches from the same device for same user at same time
        unique_together = ('device', 'zk_user_id', 'punch_time')
        ordering = ['punch_time']
        indexes = [
            models.Index(fields=['zk_user_id', 'punch_time']),
            models.Index(fields=['is_processed']),
        ]

    def __str__(self):
        return f'ZK#{self.zk_user_id} @ {self.punch_time} via {self.device.name}'