from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('role', User.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    # --- Roles ---
    ADMIN               = 'admin'
    PRINCIPAL           = 'principal'
    DEPUTY_PRINCIPAL    = 'deputy_principal'
    STOREKEEPER         = 'storekeeper'

    ROLE_CHOICES = [
        (ADMIN,             'Admin'),
        (PRINCIPAL,         'Principal'),
        (DEPUTY_PRINCIPAL,  'Deputy Principal'),
        (STOREKEEPER,       'Storekeeper'),
    ]

    username    = models.CharField(max_length=150, unique=True)
    full_name   = models.CharField(max_length=255)
    role        = models.CharField(max_length=30, choices=ROLE_CHOICES)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)  # required for Django admin access
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['full_name', 'role']

    class Meta:
        db_table = 'auth_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.full_name} ({self.get_role_display()})'

    # --- Role helpers ---
    @property
    def is_admin(self):
        return self.role == self.ADMIN

    @property
    def is_principal_or_deputy(self):
        return self.role in (self.PRINCIPAL, self.DEPUTY_PRINCIPAL)

    @property
    def is_storekeeper(self):
        return self.role == self.STOREKEEPER