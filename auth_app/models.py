from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import FileExtensionValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import serializers, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.db.models.signals import post_save
from django.dispatch import receiver

# User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

# User Model
class CustomUser(AbstractUser, PermissionsMixin):
    username = None
    email = models.EmailField(unique=True)
    is_superadmin = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_admissions = models.BooleanField(default=False)
    is_trainer = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)  # Approval required to activate account
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def get_tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

# Profile Model
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    phone_number = PhoneNumberField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    birth_date = models.DateField(null=True, blank=True)
    education = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True)
    uploaded_cv = models.FileField(
        upload_to='cv_uploads/',
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx'])],
        blank=True
    )
    cohort = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.email}"

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Report Model
class Report(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'is_student': True})
    report_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    progress_notes = models.TextField()
    problem = models.TextField()
    solve_problem = models.TextField()
    upload_file = models.FileField(upload_to='reports/', validators=[FileExtensionValidator(['pdf', 'doc', 'docx'])])

    def __str__(self):
        return self.title