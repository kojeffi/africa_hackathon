from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import EmailValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)  # Set username to email
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        # Explicitly set the username
        extra_fields['username'] = email

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    is_trainer = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    invitation_code = models.CharField(max_length=50, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    is_waiting_approval = models.BooleanField(default=False) 

    # Apply the email validator
    email = models.EmailField(
        unique=True, 
        validators=[EmailValidator()],
        error_messages={
            'unique': "This email is already taken.",
            'invalid': "Please enter a valid email address."
        }
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def save(self, *args, **kwargs):
        # Automatically set username to email if not provided
        if not self.username or self.username == "":
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email or self.username


def validate_file_type(value):
    allowed_types = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]
    if value.file.content_type not in allowed_types:
        raise ValidationError('Invalid file type. Only PDF or Word documents are allowed.')


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    phone_number = PhoneNumberField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    birth_date = models.DateField(null=True, blank=True)
    education = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True)
    uploaded_cv = models.FileField(upload_to='cv_uploads/', validators=[validate_file_type])
    cohort = models.CharField(max_length=255, blank=True, null=True) 

    def __str__(self):
        return self.user.username


class InvitationCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code
