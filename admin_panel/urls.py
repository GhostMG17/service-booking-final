from django.urls import path
from .views import manage_users, manage_bookings, update_user_role, update_booking_status, user_detail, \
    submit_review_email, reviews_list, promotions_list, create_promotion, edit_promotion, delete_promotion


urlpatterns = [
    path("users/", manage_users, name="manage_users"),
    path("bookings/", manage_bookings, name="manage_bookings"),
    path("users/update/<int:user_id>/", update_user_role, name="update_user_role"),
    path("update_booking_status/<int:booking_id>/", update_booking_status, name="update_booking_status"),
    path("user/<int:user_id>/", user_detail, name="user_detail"),
    path("submit_review_email/<int:booking_id>/", submit_review_email, name="submit_review_email"),
    path('reviews/', reviews_list, name='reviews_list'),
    path('promotions/',promotions_list, name='admin_promotions'),
    path('promotions/new/', create_promotion, name='create_promotion'),
    path('promotions/<int:pk>/edit/', edit_promotion, name='edit_promotion'),
    path('promotions/<int:pk>/delete/', delete_promotion, name='delete_promotion'),
]
