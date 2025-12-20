from django.contrib import admin
from apps.report.models import MedicalCardReport


class MedicalCardReportAdmin(admin.ModelAdmin):
    list_display = ["client", "doctor", "action", "created_at"]

    
admin.site.register(MedicalCardReport, MedicalCardReportAdmin)
