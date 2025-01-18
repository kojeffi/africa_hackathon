from django.contrib import admin
from .models import CustomUser, Profile, Report

# Customize the admin interface for CustomUser
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_superadmin', 'is_admin', 'is_admissions', 'is_trainer', 'is_student', 'is_active')
    list_filter = ('is_superadmin', 'is_admin', 'is_admissions', 'is_trainer', 'is_student', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

admin.site.register(CustomUser, CustomUserAdmin)

# Register Profile model
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'gender', 'cohort')
    search_fields = ('user__email',)

admin.site.register(Profile, ProfileAdmin)

# Register Report model
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'title', 'student')
    search_fields = ('title', 'student__email')

admin.site.register(Report, ReportAdmin)
