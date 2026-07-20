from django.contrib import admin

from .models import Gift, GiftAssignment, GiftGiver, GiftList, GiftReceiver


@admin.register(GiftReceiver, GiftGiver, GiftList, Gift, GiftAssignment)
class GiftListAdmin(admin.ModelAdmin):
    list_display = ("__str__", "created_at", "updated_at")
