from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, User_Public_Phone, User_Private_Phone, User_Type, UserSalary, UserSchedule
from modeltranslation.admin import TranslationAdmin
from django.contrib.auth.models import Permission


class UserTypeAdmin(TranslationAdmin):
    list_display = [
        "pk",
        "type_text",
    ]


class PublicPhoneAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "public_phone",
    ]


class PrivatePhoneAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "private_phone",
    ]


class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['user', 'day', 'work_start_time', 'work_end_time', 'lunch_start_time', 'lunch_end_time',
                    'is_working']
    search_fields = ['day']
    list_filter = ['user']


class UserAppAdmin(UserAdmin):
    ordering = ('-pk',)
    list_display = ('pk', "username", "user_type", 'is_staff')
    readonly_fields = ("user_auth_code", "user_code_max_try", "user_code_period")
    search_fields = ('username', 'user_firstname')
    list_filter = ('user_type', )
    fieldsets = (
        (_("Personal info",), {"fields": ("username", "user_type", 'user_firstname', 'user_lastname',
                                          'user_father_name', 'user_birthdate', 'user_gender', 'user_address',
                                          'user_citizenship', 'user_specialization', 'user_telegram', 'user_salary_percent',
                                          "user_salary_child_percent", 'user_on_place', 'user_is_active', 'user_has_car',
                                          'user_image', "user_auth_code", "user_code_max_try", "user_code_period")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )


class UserSalaryAdmin(admin.ModelAdmin):
    list_display = ["pk", "salary_for_user", "salary_amount", "created_at"]


class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename']
    search_fields = ['codename', 'name']
    list_filter = ['content_type']


admin.site.register(Permission, PermissionAdmin)
admin.site.register(User, UserAppAdmin)
admin.site.register(User_Public_Phone, PublicPhoneAdmin)
admin.site.register(User_Private_Phone, PrivatePhoneAdmin)
admin.site.register(User_Type, UserTypeAdmin)
admin.site.register(UserSalary, UserSalaryAdmin)
admin.site.register(UserSchedule, ScheduleAdmin)
