from rest_framework import serializers
from .models import CustomUser, Profile, InvitationCode
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class RegisterTrainerSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    invitation_code = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password', 'invitation_code']

    def validate(self, data):
        # Validate passwords
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")

        # Validate invitation code
        invitation_code = data.get('invitation_code')
        try:
            code = InvitationCode.objects.get(code=invitation_code)
        except InvitationCode.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation code.")

        data['invitation_code_instance'] = code
        return data

    def create(self, validated_data):
        # Pop unnecessary fields
        validated_data.pop('confirm_password')
        code_instance = validated_data.pop('invitation_code_instance')

        # Ensure that the username is set to email
        validated_data['username'] = validated_data.get('email')
        # Create user
        user = CustomUser.objects.create_user(**validated_data, is_trainer=True)

        # Mark the invitation code as used
        code_instance.used_by = user
        code_instance.save()
        return user


class RegisterStudentSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        # Ensure that the username is set to email
        validated_data['username'] = validated_data.get('email')
        user = CustomUser.objects.create_user(**validated_data, is_student=True)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone_number', 'gender', 'birth_date', 'education', 'linkedin_url', 'profile_image', 'cohort']


class LoginTrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'password']


class LoginStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'password']