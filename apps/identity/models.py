import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(email__iexact=username)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Eine E-Mail-Adresse wird benötigt.")
        user = self.model(email=self.normalize_email(email).casefold(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Die Administratormerkmale fehlen.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        db_table = "identity_users"
        constraints = [models.UniqueConstraint(Lower("email"), name="identity_email_case_unique")]

    def __str__(self):
        return self.email


class LoginBucket(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    attempts = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField()

    class Meta:
        db_table = "identity_login_buckets"
