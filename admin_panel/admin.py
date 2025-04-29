

from django.contrib import admin
from users.models import Promotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "discount_percent", "is_active", "get_is_active_now", "start_date", "end_date", "service")
    list_filter = ("start_date", "end_date", "service", "is_active")
    search_fields = ("title", "description")

    def get_is_active_now(self, obj):
        return obj.is_active_now

    get_is_active_now.short_description = 'Active Now (by date)'
    get_is_active_now.boolean = True
