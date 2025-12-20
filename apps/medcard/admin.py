from django.contrib import admin

from apps.medcard.models import Action, MedicalCard, Stage, Tooth, Xray


class ToothAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "tooth_number",
        "tooth_type",
    ]


class MedicalCardAdmin(admin.ModelAdmin):
    list_display = [
        "card_id",
        "client",
        "card_is_done",
    ]


class StageAdmin(admin.ModelAdmin):
    list_display = [
        "stage_id",
        "tooth",
        "card_id",
        "stage_is_done",
        "stage_is_paid",
        "stage_index",
    ]


class ActionAdmin(admin.ModelAdmin):
    list_display = [
        "action_id",
        "action_stage_id",
        "action_work",
        "action_quantity",
        "action_price",
        "action_is_done",
        "action_is_paid",
    ]


class XrayAdmin(admin.ModelAdmin):
    list_display = ["pk", "client"]
    list_display_links = ["pk", "client"]


admin.site.register(Stage, StageAdmin)
admin.site.register(Tooth, ToothAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(MedicalCard, MedicalCardAdmin)
admin.site.register(Xray, XrayAdmin)
