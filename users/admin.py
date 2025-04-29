from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Service, Order, Profile, Master, Salon, Review
from django.contrib import admin
from .models import Booking



class CustomUserAdmin(UserAdmin):
    # Добавляем full_name в список отображаемых полей
    list_display = ('username', 'email', 'full_name', 'is_staff', 'is_superuser', 'is_active', 'is_owner')

    # Добавляем full_name в фильтры
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_owner')

    # Добавляем full_name в форму редактирования
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {'fields': ('is_owner', 'full_name')}),  # Добавляем full_name в редактируемую форму
    )

    # Добавляем full_name в список полей, которые можно редактировать
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'fields': ('username', 'email', 'phone_number', 'full_name', 'password1', 'password2', 'role')
        }),
    )

# Регистрируем CustomUserAdmin для модели CustomUser
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
    list_display = ("name", "role", "service", "salon", "experience_display", "appointment_count")
    list_filter = ("salon", "role")
    search_fields = ("name", "salon__name")

    def appointment_count(self, obj):
        return obj.appointment_count()
    appointment_count.short_description = "Appointments"

    def experience_display(self, obj):
        return obj.experience_display()  # Отображение опыта с форматом, который ты хочешь

    experience_display.short_description = "Experience (years)"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'master', 'rating', 'comment', 'created_at')  # Which fields to show in the list
    list_filter = ('rating', 'service', 'master')  # Filters in the admin
    search_fields = ('user__username', 'service__name', 'master__name', 'comment')  # Fields to search by
