from doctest import master
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.timezone import now
from users.models import CustomUser
from .decorators import owner_required
from users.models import Booking
from users.models import Review
from users.models import Master


@login_required
@owner_required
def manage_users(request):
    users = CustomUser.objects.all()

    # Get filter parameters from the request
    username_query = request.GET.get('username', '').strip()
    role_query = request.GET.get('role', '')

    if username_query:
        users = users.filter(username__icontains=username_query)

    if role_query:
        users = users.filter(role=role_query)

    return render(request, 'manage_users.html', {'users': users})


@login_required
def update_user_role(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == "POST":
        new_role = request.POST.get("role")
        user.is_owner = new_role == "owner"  # If "owner" is selected, set to True
        user.save()
    return redirect("manage_users")


@login_required
@owner_required
def manage_bookings(request):
    status_filter = request.GET.get('status', '')  # Get status from the request (GET)

    if status_filter:  # If a status is selected, filter bookings
        bookings = Booking.objects.filter(status=status_filter)
    else:
        bookings = Booking.objects.all()  # If no filter is selected, show all

    return render(request, 'manage_bookings.html', {'bookings': bookings})


@login_required
def update_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == "POST":
        new_status = request.POST.get("status")

        # ❌ Prevent changes to completed booking
        if booking.status == "completed":
            messages.error(request, "Cannot change a completed booking.")
            return redirect("manage_bookings")

        # ❌ Prevent changes to canceled booking
        if booking.status == "canceled" and new_status in ["confirmed", "completed"]:
            messages.error(request, "Cannot change a canceled booking.")
            return redirect("manage_bookings")

        # ❌ Prevent completing an unconfirmed booking
        if new_status == "completed" and booking.status != "confirmed":
            messages.error(request, "Booking must be confirmed before completing.")
            return redirect("manage_bookings")

        # ❌ Prevent confirming a booking with a past date
        if new_status == "confirmed" and booking.booking_date < now().date():
            messages.error(request, "Cannot confirm a booking with a past date.")
            return redirect("manage_bookings")

        # If completed, send an email asking for a review
        if new_status == "completed":
            print("Status updated to 'Completed', sending email")
            send_review_request_email(booking, request)

        # ✅ Update the status if all checks pass
        booking.status = new_status
        booking.save()
        messages.success(request, "Status successfully updated.")

    return redirect("manage_bookings")


def send_review_request_email(booking, request):
    """Sends an email to the client with links to rate the service and master"""

    base_url = request.build_absolute_uri(reverse('submit_review_email', args=[booking.id]))

    # Make sure the booking has a master
    master_id = booking.master.id if booking.master else ""

    # Generate rating links (1-5 stars)
    review_links = "\n".join([
        f"⭐ {i} - {base_url}?rating={i}&master_id={master_id}"
        for i in range(1, 6)
    ])

    message = f"""
    Hello, {booking.user.username}!

    Your booking is completed. We value your feedback!

    Rate our service and the work of the master by simply clicking the star you prefer:

    {review_links}

    Thank you for your review! 🌟
    """

    send_mail(
        "Rate our service ⭐",
        message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.user.email],
        fail_silently=False,
    )


def submit_review_email(request, booking_id):
    """Handles the review submitted from the email link"""
    rating = request.GET.get('rating')
    master_id = request.GET.get('master_id')

    if not rating or not master_id:
        return HttpResponse("Invalid request.", status=400)

    booking = get_object_or_404(Booking, id=booking_id)
    service = booking.service
    master = get_object_or_404(Master, id=master_id)

    # Create the review, ensuring the booking is provided
    Review.objects.create(
        booking=booking,
        user=booking.user,
        service=service,
        master=master,
        rating=int(rating),
        comment="Rating from email"
    )

    return HttpResponse("Thank you for your review! 🌟", status=200)


def reviews_list(request):
    """Displays the list of reviews in the admin panel"""
    reviews = Review.objects.all().order_by('-created_at')  # Latest reviews first
    return render(request, 'review_list.html', {'reviews': reviews})


@login_required
def user_detail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    bookings = Booking.objects.filter(user=user).order_by("-booking_date")

    return render(request, "user_detail.html", {"user": user, "bookings": bookings})
