from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth import logout
from .models import CustomUser, Profile
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from .serializers import (RegisterTrainerSerializer, RegisterStudentSerializer,
                          ProfileSerializer, LoginTrainerSerializer,LoginStudentSerializer)


class RegisterTrainerAPIView(APIView):
    def post(self, request):
        serializer = RegisterTrainerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "You have successfully registered",
                    "result_code": 1,
                    "data": serializer.data
                }, 
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "message": "Account Registration failed",
                "result_code": 0,
                "data": serializer.errors
            }, 
            status=status.HTTP_400_BAD_REQUEST
        )

class LoginTrainerAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {
                    "message": "Email and password are required.",
                    "result_code": 0,
                    "data": []
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_trainer:

                user_data = {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_trainer": user.is_trainer,
                    "password": user.password,
                }
                return Response(
                    {
                        "message": f"You have successfully logged into your account. You can close the window and Begin",
                        "result_code": 1,
                        "data": user_data
                    }, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "message": "No Trainer Account with the provided credentials Found.",
                        "result_code": 0,
                        "data": []
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {
                "message": "Invalid email or Password",
                "result_code": 0,
                "data": []
            }, 
            status=status.HTTP_400_BAD_REQUEST
        )

class RegisterStudentAPIView(APIView):
    def post(self, request):
        serializer = RegisterStudentSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "Account created successfully. Please complete your profile and Submit for Approval.",
                    "result_code": 1,
                    "data": {"id": user.id}
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "message": "Account registration failed.",
                "result_code": 0,
                "data": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

class SubmitProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Verifying your details, you will receive an email notification Upon Approval",
                    "result_code": 1,
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                "message": "Failed to submit profile.",
                "result_code": 0,
                "data": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

class ReviewStudentAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only trainers/superadmin should access this

    def get(self, request):
        if not request.user.is_staff:  # Ensure only trainers/superadmins can access this
            return Response(
                {"message": "Unauthorized", "result_code": 0}, status=status.HTTP_403_FORBIDDEN
            )
        students = CustomUser.objects.filter(is_student=True, is_approved=False)
        data = [{"id": student.id, "email": student.email, "profile": ProfileSerializer(student.profile).data}
                for student in students]
        return Response({"students": data})

    def post(self, request, student_id):
        action = request.data.get("action")
        cohort = request.data.get("cohort")

        try:
            student = CustomUser.objects.get(id=student_id, is_student=True)
        except CustomUser.DoesNotExist:
            return Response(
                {"message": "Student not found.", "result_code": 0}, status=status.HTTP_404_NOT_FOUND
            )

        if action == "approve":
            student.is_approved = True
            student.profile.cohort = cohort
            student.profile.save()
            student.save()

            # Send approval email
            send_mail(
                "Account Approved",
                f"Hi {student.first_name}, your account has been approved. You can now log in.",
                settings.DEFAULT_FROM_EMAIL,
                [student.email],
            )

            return Response({"message": "Student approved."})
        elif action == "reject":
            # Send rejection email
            send_mail(
                "Account Rejected",
                f"Hi {student.first_name}, your account registration has been rejected.",
                settings.DEFAULT_FROM_EMAIL,
                [student.email],
            )
            student.delete()
            return Response({"message": "Student rejected."})

        return Response({"message": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)
    

class LoginStudentAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {
                    "message": "Email and password are required.",
                    "result_code": 0,
                    "data": []
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_student:

                 # Check if the student account is approved
                if not user.is_approved:
                    return Response(
                        {
                            "message": "Your account is not yet approved. Please wait for approval.",
                            "result_code": 0,
                            "data": []
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )
                user_data = {
                    
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_student": user.is_student,
                    "password": user.password,
                }
                return Response(
                    {
                        "message": f"You have successfully logged into your account. You can close the window and Begin",
                        "result_code": 1,
                        "data": user_data
                    }, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "message": "No Student Account with the provided credentials Found.",
                        "result_code": 0,
                        "data": []
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {
                "message": "Invalid email or password",
                "result_code": 0,
                "data": []
            }, 
            status=status.HTTP_400_BAD_REQUEST
        )

class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(
            {
                "message": "Profile retrieved successfully",
                "result_code": 1,
                "data": serializer.data
            }
        )

    def post(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Profile updated successfully",
                    "result_code": 1,
                    "data": serializer.data
                }
            )
        return Response(
            {
                "message": "Failed to update profile",
                "result_code": 0,
                "data": serializer.errors
            }, 
            status=status.HTTP_400_BAD_REQUEST
        )

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(
            {
                "message": "Successfully logged out.",
                "result_code": 1,
                "data": []
            }, 
            status=status.HTTP_200_OK
        )
class PasswordResetRequestAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {
                    "message": "Email is required.",
                    "result_code": 0,
                    "data": []
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {
                    "message": "No user with this email address found.",
                    "result_code": 0,
                    "data": []
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate token and URL
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.id))
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

        # Send email
        send_mail(
            subject="Password Reset Request",
            message=f"Hi {user.first_name},\n\nClick the link below to reset your password:\n{reset_url}\n\nIf you didn't request this, please ignore this email.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response(
            {
                "message": "Password reset link has been sent to your email.",
                "result_code": 1,
                "data": []
            },
            status=status.HTTP_200_OK
        )

class PasswordResetConfirmAPIView(APIView):
    def post(self, request, uidb64, token):
        new_password = request.data.get("new_password")
        confirm_new_password = request.data.get("confirm_new_password")

        # Validate passwords are provided
        if not new_password or not confirm_new_password:
            return Response(
                {
                    "message": "Both 'new_password' and 'confirm_new_password' are required.",
                    "result_code": 0,
                    "data": []
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if passwords match
        if new_password != confirm_new_password:
            return Response(
                {
                    "message": "Passwords do not match.",
                    "result_code": 0,
                    "data": []
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(id=uid)
        except (ValueError, CustomUser.DoesNotExist):
            return Response(
                {
                    "message": "Invalid user ID.",
                    "result_code": 0,
                    "data": []
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate the token
        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response(
                {
                    "message": "Invalid or expired Link.",
                    "result_code": 0,
                    "data": []
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set the new password
        user.set_password(new_password)
        user.save()

        return Response(
            {
                "message": "Password has been reset successfully.",
                "result_code": 1,
                "data": []
            },
            status=status.HTTP_200_OK
        )
