from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "diagnostic_test", "centre", "status", "appointment_datetime"]
    list_filter = ["status", "centre"]
    search_fields = ["user__username", "id"]
