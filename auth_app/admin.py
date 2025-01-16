from django.contrib import admin
from .models import InvitationCode, Profile, CustomUser
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'gender', 'birth_date',
                    'education', 'linkedin_url','uploaded_cv','profile_image')
    search_fields = ('user__username', 'phone_number', 'education')

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):  # Use UserAdmin instead of ModelAdmin
    list_display = ('first_name', 'last_name', 'email', 'is_trainer', 'is_student', 'invitation_code', 'is_approved', 'is_rejected', 'is_waiting_approval', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_trainer', 'is_student', 'is_approved', 'is_rejected', 'is_waiting_approval', 'is_active')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),  # Permissions fields
        ('Account Type', {'fields': ('is_student', 'is_trainer', 'is_approved', 'is_rejected', 'is_waiting_approval', 'invitation_code')}),  # Custom fields
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_student', 'is_trainer', 'is_approved', 'is_rejected', 'is_waiting_approval', 'invitation_code'),
        }),
    )


@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'created_at')  # Ensure these fields exist in InvitationCode model
    search_fields = ('code',)
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
