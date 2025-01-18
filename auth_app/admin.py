from django.contrib import admin
from .models import CustomUser, Profile, Report, EducationLevel, EducationDetail, Cohort, Unit, TrainerAssignment, \
    StudentCohortAssignment


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


@admin.register(EducationLevel)
class EducationLevelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(EducationDetail)
class EducationDetailAdmin(admin.ModelAdmin):
    list_display = ['profile', 'level_of_education', 'school_name', 'start_date', 'end_date']
    list_filter = ['level_of_education']

@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(TrainerAssignment)
class TrainerAssignmentAdmin(admin.ModelAdmin):
    list_display = ['trainer', 'cohort', 'unit']
    list_filter = ['cohort', 'unit', 'trainer']

@admin.register(StudentCohortAssignment)
class StudentCohortAssignmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'cohort', 'unit']
    list_filter = ['cohort', 'unit', 'student']