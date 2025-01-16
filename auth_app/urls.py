from django.urls import path
from .views import RegisterTrainerAPIView, RegisterStudentAPIView, ProfileAPIView, LoginTrainerAPIView, LoginStudentAPIView, LogoutAPIView, PasswordResetRequestAPIView, PasswordResetConfirmAPIView, SubmitProfileAPIView, ReviewStudentAPIView

urlpatterns = [
    path('register/trainer/', RegisterTrainerAPIView.as_view(), name='register_trainer'),
    path('register/student/', RegisterStudentAPIView.as_view(), name='register_student'),
    path('profile/', ProfileAPIView.as_view(), name='profile'),
    path('login/trainer/', LoginTrainerAPIView.as_view(), name='login_trainer'),
    path('login/student/', LoginStudentAPIView.as_view(), name='student_trainer'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('password-reset/', PasswordResetRequestAPIView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),
     path("register-student/", RegisterStudentAPIView.as_view(), name="register-student"),
    path("submit-profile/", SubmitProfileAPIView.as_view(), name="submit-profile"),
    path("review-student/<int:student_id>/", ReviewStudentAPIView.as_view(), name="review-student"),
]
