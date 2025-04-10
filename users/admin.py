from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Service, Order, Profile, Master, Salon, Review
from django.contrib import admin
from .models import Booking

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'is_owner')  # Added is_owner
    list_filter = ('is_staff', 'is_superuser', 'is_owner')  # Filter by is_owner
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {'fields': ('is_owner',)}),  # Added in the edit form
    )

admin.site.register(CustomUser, CustomUserAdmin)


# Registering the Service model
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'availability')  # Which fields to display in the list
    search_fields = ('name', 'description')  # Which fields to search by
    list_filter = ('availability',)  # Filtering by availability
    ordering = ('price',)  # Sorting by price


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'date', 'status')
    list_filter = ('status', 'date')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'date_of_birth', 'address', 'bio')
    search_fields = ('user__username', 'full_name')
    list_filter = ('date_of_birth',)



@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'booking_date', 'booking_time', 'status')
    list_filter = ('booking_date', 'status')
    search_fields = ('user__username', 'service__name')


@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = ("name", "location")  # Display name and location in the list
    search_fields = ("name", "location")  # Searching by name and location


@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "service", "salon")  # Added salon in the list display
    list_filter = ("salon", "role")  # Filtering by salon
    search_fields = ("name", "salon_name")  # Searching by name and salon name


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'master', 'rating', 'comment', 'created_at')  # Which fields to show in the list
    list_filter = ('rating', 'service', 'master')  # Filters in the admin
    search_fields = ('user__username', 'service__name', 'master__name', 'comment')  # Fields to search by
