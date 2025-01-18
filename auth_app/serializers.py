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

from auth_app.models import CustomUser, Profile, Report, EducationDetail, Cohort, Unit, TrainerAssignment, \
    StudentCohortAssignment


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


from rest_framework import serializers

class EducationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationDetail
        fields = ['id', 'level_of_education', 'school_name', 'field_of_study', 'start_date', 'end_date', 'grade']


class ProfileSerializer(serializers.ModelSerializer):
    education_details = EducationDetailSerializer(many=True)

    class Meta:
        model = Profile
        fields = ['phone_number', 'gender', 'birth_date', 'education_details', 'linkedin_url', 'profile_image', 'uploaded_cv']

    def create(self, validated_data):
        education_details_data = validated_data.pop('education_details', [])
        profile = super().create(validated_data)
        for edu_data in education_details_data:
            EducationDetail.objects.create(profile=profile, **edu_data)
        return profile

    def update(self, instance, validated_data):
        education_details_data = validated_data.pop('education_details', [])
        instance = super().update(instance, validated_data)

        # Update or create education details
        for edu_data in education_details_data:
            edu_id = edu_data.pop('id', None)
            if edu_id:
                # Update existing education detail
                EducationDetail.objects.filter(id=edu_id, profile=instance).update(**edu_data)
            else:
                # Create new education detail
                EducationDetail.objects.create(profile=instance, **edu_data)
        return instance


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


class CohortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = ['id', 'name', 'description']

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'name', 'description']

class TrainerAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerAssignment
        fields = ['id', 'trainer', 'cohort', 'unit']

class StudentCohortAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentCohortAssignment
        fields = ['id', 'student', 'cohort', 'unit']

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'report_id',
            'student',
            'trainer',
            'cohort',
            'unit',
            'title',
            'progress_notes',
            'problem',
            'solve_problem',
            'upload_file'
        ]
