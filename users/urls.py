from django.urls import include
from django.contrib.auth.views import  LogoutView
from django.urls import path
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views
from .views import available_slots, get_services, get_masters, cancel_booking, booking_page, top_masters, login_user, \
    cancel_booking_by_url
from django.conf import settings


# a router for handling API endpoints (Django Rest Framework)
router = DefaultRouter()

# List of all URL patterns for the app
urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', login_user, name='login'),
    # API endpoint for creating a booking
    path('api/create_booking/', views.create_booking, name='create_booking'),
    path("create_booking/", booking_page, name="booking_page"),
    path('service_list/', views.service_list, name='service_list'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    # Include API URLs from the DRF router
    path('api/', include(router.urls)),
    path('api/available-slots/', available_slots, name='available_slots'),
    path('api/services/', get_services, name='get_services'),
    # path("api/cancel_booking/", cancel_booking, name="cancel_booking"),
    path("bookings/<int:booking_id>/cancel/", cancel_booking_by_url, name="cancel_booking_by_url"),

    path("api/masters/", get_masters, name="get_masters"),
    path('salon/<int:salon_id>/', views.salon_detail, name='salon_detail'),
    path('salons/', views.salons, name = 'salons'),
    path('masters/', views.masters, name='masters'),
    path('top-masters/', top_masters, name='top-master'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


