from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ApprovalView, LogoutView, TrainerRegistrationView, StudentRegistrationView, TrainerLoginView, \
    StudentLoginView

router = DefaultRouter()
# router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    # path('login/', LoginView.as_view(), name='login'),
    # path('register/', RegistrationView.as_view(), name='register'),
    path('approve/', ApprovalView.as_view(), name='approve'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include(router.urls)),
    # path('create-superadmin/', CreateSuperAdminView.as_view(), name='create-superadmin'),
    path('register/trainer/', TrainerRegistrationView.as_view(), name='register-trainer'),
    path('register/student/', StudentRegistrationView.as_view(), name='register-student'),
    path('login/trainer/', TrainerLoginView.as_view(), name='login-trainer'),
    path('login/student/', StudentLoginView.as_view(), name='login-student'),
]
