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
from django.db.models.signals import post_save
from django.dispatch import receiver

from auth_app.models import CustomUser, Profile, Report, EducationDetail
from auth_app.serializers import UserSerializer, ReportSerializer, EducationDetailSerializer


# Signal to send an email when a user is activated
@receiver(post_save, sender=CustomUser)
def send_activation_email(sender, instance, created, **kwargs):
    if not created and instance.is_active:  # Only send if user was updated and marked active
        subject = "Your Account Has Been Approved"
        message = "Your account has been approved. You can now log in to the system."
        recipient_email = instance.email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[recipient_email],
        )


class TrainerRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        required_fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password']

        for field in required_fields:
            if field not in data:
                return Response({'detail': f'Missing field: {field}'}, status=status.HTTP_400_BAD_REQUEST)

        if data['password'] != data['confirm_password']:
            return Response({'detail': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            if not user.email.endswith('@200zynamis.co.ke'):
                return Response({'detail': 'Trainer must use an organization email.'}, status=status.HTTP_400_BAD_REQUEST)

            user.is_trainer = True  # Mark as trainer
            user.is_active = False  # Require approval
            user.save()
            return Response({'detail': 'Trainer registration successful. Awaiting approval.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data

        # Combine all required fields for both user and profile
        required_user_fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password']
        required_profile_fields = ['phone_number', 'gender', 'birth_date', 'education', 'linkedin_url']

        # Validate user fields
        for field in required_user_fields:
            if not data.get(field):
                return Response({'detail': f'Missing required field: {field}'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate passwords
        if data['password'] != data['confirm_password']:
            return Response({'detail': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate profile fields
        profile_data = data.get('profile', {})
        for field in required_profile_fields:
            if not profile_data.get(field):
                return Response({'detail': f'Missing required profile field: {field}'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate and save the user
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_student = True
            user.is_active = False  # Require approval
            user.save()

            # Save the profile data
            profile = user.profile
            for field, value in profile_data.items():
                setattr(profile, field, value)
            profile.save()

            return Response({'detail': 'Student registration successful. Awaiting approval.'}, status=status.HTTP_201_CREATED)

        # Return serializer errors if user validation fails
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
            if request.user.is_admissions or request.user.is_superadmin:
                user.is_active = True
                user.save()
                return Response({'detail': 'User approved successfully. Email notification sent.'}, status=status.HTTP_200_OK)
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return Response({'detail': 'Authorization header missing.'}, status=status.HTTP_400_BAD_REQUEST)

            token = auth_header.split(' ')[1]
            refresh = RefreshToken(token)
            refresh.blacklist()

            return Response({'detail': 'Logout successful.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': f'Error: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class ReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_trainer:
            return Report.objects.filter(student__profile__cohort=user.profile.cohort)
        elif user.is_admissions or user.is_superadmin:
            return Report.objects.all()
        return Report.objects.none()


class TrainerLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = CustomUser.objects.get(email=email, is_trainer=True)
            if not user.check_password(password):
                return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)
            if not user.is_active:
                return Response({'detail': 'Account is not approved yet.'}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            return Response({
                'detail': 'Login successful.',
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'is_trainer': user.is_trainer
                },
                'Access Token': str(refresh.access_token),
                'Refresh Token': str(refresh),
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Trainer not found.'}, status=status.HTTP_404_NOT_FOUND)


class StudentLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = CustomUser.objects.get(email=email, is_student=True)
            if not user.check_password(password):
                return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)
            if not user.is_active:
                return Response({'detail': 'Account is not approved yet.'}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            return Response({
                'detail': 'Login successful.',
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'is_student': user.is_student
                },
                'Access Token': str(refresh.access_token),
                'Refresh Token': str(refresh),
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

# Add  education
class EducationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EducationDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(profile=request.user.profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        education_details = EducationDetail.objects.filter(profile=request.user.profile)
        serializer = EducationDetailSerializer(education_details, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

