import json
from datetime import timedelta, datetime, timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db import models
from django.db.models import Avg
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .forms import CustomUserCreationForm, UserUpdateForm, ProfileForm, ReviewForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from .models import Booking, ServiceFilterForm, Service, Profile, Master
from .serializers import BookingSerializer, ServiceSerializer
from django.contrib import messages


def home(request):
    services = Service.objects.all()[:5]
    return render(request, 'home.html',{'services': services})


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Set user as inactive
            user.save()

            # Generate token for email confirmation
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))

            # Get current domain
            domain = get_current_site(request).domain
            activation_url = f'http://{domain}/activate/{uid}/{token}/'

            # Send email with activation link
            subject = 'Email Confirmation for Your Registration'
            message = render_to_string('activation_email.html', {
                'user': user,
                'activation_url': activation_url,
            })
            send_mail(subject, message, 'muhammadkhongaybulloev17@gmail.com', [user.email])

            messages.success(request, "Registration successful! Please check your email to activate your account.")
            return redirect('home')
        else:
            messages.error(request, "An error occurred. Please check the form and try again.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You have successfully logged in!")
            return redirect('home')
        else:
            messages.error(request, "Error: incorrect username or password.")
    return render(request, 'login.html')


def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')
    return redirect('home')


def booking_page(request):
    return render(request, "booking_form.html")


@csrf_exempt
def create_booking(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service_id = data.get("service_id")
            master_id = data.get("master_id")
            booking_date = data.get("date")
            booking_time = data.get("time")
            user = request.user

            if not (service_id and master_id and booking_date and booking_time):
                return JsonResponse({"error": "All fields are required!"}, status=400)

            try:
                service = Service.objects.get(id=service_id)
                master = Master.objects.get(id=master_id)
                salon = master.salon
            except (Service.DoesNotExist, Master.DoesNotExist):
                return JsonResponse({"error": "Service or master not found!"}, status=404)

            booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
            booking_time = datetime.strptime(booking_time, "%H:%M").time()

            if Booking.objects.filter(master=master, booking_date=booking_date, booking_time=booking_time).exists():
                return JsonResponse({"error": "This master is already booked at the selected time!"}, status=400)

            booking = Booking.objects.create(
                user=user,
                service=service,
                master=master,
                booking_date=booking_date,
                booking_time=booking_time,
                status="pending"
            )

            # Send email
            subject = "Booking Confirmation"
            message = f"""

Hello, {user.username}!

You have successfully booked a service.

📅 Date: {booking_date.strftime('%d %B %Y')}
⏰ Time: {booking_time.strftime('%H:%M')}

Master: {master.name} ({master.role})
Service: {service.name}
💰 Price: {service.price} so’m

🗒 Salon: {salon.name}
📍 Address: {salon.location}
📧 Contact: {salon.contact_email}

Thank you for using our service!
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return JsonResponse({"message": "Booking successful, please check your email"}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Error in JSON format!"}, status=400)

    return JsonResponse({"error": "Method not supported!"}, status=405)

@csrf_exempt
def cancel_booking(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            booking_id = data.get("booking_id")

            if not booking_id:
                return JsonResponse({"success": False, "error": "Booking ID not provided!"}, status=400)

            booking = Booking.objects.get(id=booking_id)

            # Check if it can be canceled
            now = datetime.now().date()
            if booking.booking_date < now:
                return JsonResponse({"success": False, "error": "Cannot cancel past booking!"}, status=400)

            user_email = booking.user.email
            service_name = booking.service.name
            booking_date = booking.booking_date.strftime("%d.%m.%Y")
            booking_time = booking.booking_time.strftime("%H:%M")

            booking.delete()  # ❗ Delete the booking

            # 🔔 Send email to user
            send_mail(
                "Booking Canceled",
                f"Your booking for {service_name} on {booking_date} at {booking_time} has been successfully canceled.",
                "muhammadkhongaybulloev17@gmail.com",  # Sender
                [user_email],  # Recipient
                fail_silently=False,
            )

            return JsonResponse({"success": True, "message": "Booking canceled, notification sent!"})

        except Booking.DoesNotExist:
            return JsonResponse({"success": False, "error": "Booking not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "JSON format error!"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error: {str(e)}"}, status=400)

    return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)


def booking_details(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)

        response_data = {
            "booking_id": booking.id,
            "user": booking.user.username,
            "date": booking.booking_date.strftime('%d %B %Y'),
            "time": booking.booking_time.strftime('%H:%M'),
            "master_name": booking.master.name,
            "master_role": booking.master.role,
            "service": booking.service.name,
            "price": f"{booking.service.price} so’m",
            "salon": booking.master.salon.name,
            "location": booking.master.salon.location,
            "contact": booking.master.salon.contact_email
        }

        return JsonResponse(response_data)

    except Booking.DoesNotExist:
        return JsonResponse({"error": "Booking not found!"}, status=404)


def available_slots(request):
    service_id = request.GET.get("service_id")
    master_id = request.GET.get("master_id")
    date = request.GET.get("date")

    if not (service_id and master_id and date):
        return JsonResponse({"error": "Please specify the service, master, and date!"}, status=400)

    try:
        service = Service.objects.get(id=service_id)
        master = Master.objects.get(id=master_id)
    except (Service.DoesNotExist, Master.DoesNotExist):
        return JsonResponse({"error": "Service or master not found!"}, status=404)

    date = datetime.strptime(date, "%Y-%m-%d").date()

    # All available slots (example)
    all_slots = ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]

    # Get already booked slots for the master
    booked_slots = Booking.objects.filter(
        master=master, booking_date=date
    ).values_list("booking_time", flat=True)

    # Remove booked slots
    available_slots = [slot for slot in all_slots if slot not in booked_slots]

    return JsonResponse({"available_slots": available_slots})


def view_bookings(request):
    if request.user.is_authenticated:
        bookings = Booking.objects.filter(user=request.user)
        return render(request, 'view_bookings.html', {'bookings': bookings})
    else:
        messages.error(request, 'Please log in to view your bookings.')
        return redirect('login')


def service_list(request):
    services = Service.objects.all()
    form = ServiceFilterForm(request.GET)

    if form.is_valid():
        category = form.cleaned_data.get('category')
        if category:
            services = services.filter(category=category)

        price_min = form.cleaned_data.get('price_min')
        if price_min:
            services = services.filter(price__gte=price_min)

        price_max = form.cleaned_data.get('price_max')
        if price_max:
            services = services.filter(price__lte=price_max)

        duration_min = form.cleaned_data.get('duration_min')
        if duration_min:
            services = services.filter(duration__gte=duration_min)

        duration_max = form.cleaned_data.get('duration_max')
        if duration_max:
            services = services.filter(duration__lte=duration_max)

        sort_by = form.cleaned_data.get('sort_by')
        if sort_by:
            services = services.order_by(sort_by)

    return render(request, 'service_list.html', {'services': services, 'form': form})


def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    return render(request, 'service_detail.html', {'service': service})


def service_search(request):
    query = request.GET.get('query', '')
    services = Service.objects.all()

    if query:
        services = services.filter(
            models.Q(name__icontains=query) | models.Q(description__icontains=query)
        )

    return render(request, 'service_search.html', {'services': services})

def send_verification_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(user.pk.encode())

    # Activation URL
    activation_link = f"{get_current_site()}/activate/{uid}/{token}/"

    subject = 'Email Verification'
    message = render_to_string('activation_email.html', {
        'user': user,
        'activation_link': activation_link
    })
    send_mail(
        subject,
        message,
        'muhammadkhongaybulloev17@gmail.com',  # Sender email
        [user.email],
        fail_silently=False
    )


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode('utf-8')
        user = get_user_model().objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Your account has been successfully activated!")
            return redirect('login')  # Redirect to login page
        else:
            messages.error(request, "Unable to activate your account. Please check the link.")
            return redirect('home')
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        messages.error(request, "Activation error.")
        return redirect('home')


@login_required
def profile(request):
    user = request.user

    # Get or create profile
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user)

    # Get booking history with filtering
    bookings = Booking.objects.filter(user=user)
    if 'status' in request.GET:
        bookings = bookings.filter(status=request.GET['status'])

    # Handle profile update form
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    # Send data to the template
    return render(request, "profile.html", {
        "user": user,
        "profile": profile,
        "form": form,
        "bookings": bookings
    })


@login_required
def update_profile(request):
    user = request.user
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=user)

    return render(request, 'update_profile.html', {'form': form})

User = get_user_model()
def check_username(request):
    username = request.GET.get('username', '')
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

class BookingViewSet(viewsets.ModelViewSet):
    """ CRUD for bookings """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


@api_view(['GET'])
def available_slots(request):
    """ Get available slots for the selected day """

    service_id = request.GET.get('service_id')
    date_str = request.GET.get('date')

    if not service_id or not date_str:
        return Response({"error": "service_id and date are required"}, status=400)

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()  # Convert string to date
    except ValueError:
        return Response({"error": "Invalid date format. Please use YYYY-MM-DD."}, status=400)

    service = Service.objects.get(id=service_id)
    duration = service.duration

    start_time = datetime.strptime("09:00", "%H:%M")  # Start of working hours
    end_time = datetime.strptime("18:00", "%H:%M")  # End of working hours

    available_slots = []
    current_time = start_time

    while current_time + timedelta(minutes=duration) <= end_time:
        # Check if this slot is taken
        if not Booking.objects.filter(
                service=service,
                booking_date=date,
                booking_time=current_time.time()
        ).exists():
            available_slots.append(current_time.strftime("%H:%M"))

        current_time += timedelta(minutes=30)  # Check every 30 minutes

    return Response({"available_slots": available_slots})


@api_view(['GET'])
def get_services(request):
    """ Get a list of all services """
    services = Service.objects.all()
    serializer = ServiceSerializer(services, many=True)
    return Response(serializer.data)


def get_masters(request):
    service_id = request.GET.get("service_id")

    if not service_id:
        return JsonResponse({"error": "service_id is required"}, status=400)

    masters = Master.objects.filter(service_id=service_id).values("id", "name")

    return JsonResponse(list(masters), safe=False)


@login_required
def add_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Check if a review already exists
    if hasattr(booking, 'review'):
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.user = request.user
            review.master = booking.master  # Link with the master
            review.save()
            return redirect('booking_detail', booking_id=booking.id)  # Redirect after successful review
    else:
        form = ReviewForm()

    return render(request, "add_review.html", {"form": form, "booking": booking})


def top_masters(request):
    masters = (
        Master.objects.annotate(avg_rating=Avg("reviews__rating"))  # Average rating
        .order_by("-avg_rating")[:5]  # Top 5 by rating
    )

    data = [
        {
            "id": master.id,
            "name": master.name,
            "rating": round(master.avg_rating, 1) if master.avg_rating else "No reviews",
        }
        for master in masters
    ]

    return JsonResponse(data, safe=False)

