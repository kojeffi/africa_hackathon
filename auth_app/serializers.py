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

from auth_app.models import CustomUser, Profile, Report


class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email', 'password', 'confirm_password', 'is_superadmin', 'is_admin', 'is_admissions', 'is_trainer', 'is_student', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')  # Remove the confirm_password field before creating the user
        user = CustomUser.objects.create_user(**validated_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


class UserResponseSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(source='profile.profile_image', read_only=True)
    cohort = serializers.CharField(source='profile.cohort', read_only=True)
    phone_number = serializers.CharField(source='profile.phone_number', read_only=True)
    gender = serializers.CharField(source='profile.gender', read_only=True)
    birth_date = serializers.DateField(source='profile.birth_date', read_only=True)
    education = serializers.CharField(source='profile.education', read_only=True)
    linkedin_url = serializers.URLField(source='profile.linkedin_url', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'email', 'is_superadmin', 'is_admin',
            'is_admissions', 'is_trainer', 'is_student', 'is_active', 'profile_picture',
            'cohort', 'phone_number', 'gender', 'birth_date', 'education', 'linkedin_url'
        ]
