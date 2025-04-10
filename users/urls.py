from django.urls import include, path
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

from django.contrib.auth import views as auth_views
from .views import available_slots, get_services, get_masters, cancel_booking, add_review, booking_page, top_masters

router = DefaultRouter()

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('api/create_booking/', views.create_booking, name='create_booking'),
    path('view_bookings/', views.view_bookings, name='view_bookings'),
    path('service_list/', views.service_list, name='service_list'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    path('search/', views.service_search, name='service_search'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('profile/', views.profile, name='profile'),
    path('check-username/', views.check_username, name='check_username'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('api/', include(router.urls)),
    path('api/available-slots/', available_slots, name='available_slots'),
    path('api/services/', get_services, name='get_services'),
    path("create_booking/", booking_page, name="booking_page"),
    path("api/cancel_booking/", cancel_booking, name="cancel_booking"),
    path("api/available-slots/", available_slots, name="available_slots"),
    path("api/masters/", get_masters, name="get_masters"),
    path("booking/<int:booking_id>/review/", add_review, name="add_review"),
    path('top-masters/', top_masters, name='top-masters'),
]

#dasdasd
