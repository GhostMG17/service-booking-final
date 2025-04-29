""" IMPORT NECESSARY  MODULES """
import json
from datetime import timedelta, datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMultiAlternatives
from django.db.models import Avg
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .forms import CustomUserCreationForm, UserUpdateForm, ProfileForm, ReviewForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from .models import Booking, ServiceFilterForm, Service, Profile, Master, Promotion, Salon
from .serializers import ServiceSerializer
from django.contrib import messages
from django.utils import timezone


""" HOMEPAGE VIEW FUNCTION"""
def home(request):
    services = Service.objects.all()[:5]

    # here i am fetching top 5 masters with the highest rating
    top_masters = (
        Master.objects.annotate(avg_rating=Avg("reviews__rating")) # calulcation of average rating
        .filter(avg_rating__isnull=False) # Exclude masters without reviews
        .order_by("-avg_rating")[:5] # and order by average rating in desc order showing only 5 masters
    )

    #  Get the current date for the promotion stuff logic
    current_date = timezone.now().date()

    # i filter promotion by its startdate enddate
    promotions = Promotion.objects.filter(
        start_date__lte=current_date, # it started before or today
        end_date__gte=current_date, # it ends after or today
        is_active=True # they must be active
    ).select_related('service') # Optimize query by preloading related service

    # Preparing the data to pass into the template
    context = {
        "services": services,
        "top_masters": top_masters,
        "promotions": promotions,
    }

    # render the homepage with the provided context
    return render(request, 'home/home.html', context)



""" USER REGISTRATION VIEW FUNCTION """
def register(request):
    # Check if the request method is POST (form submission)
    if request.method == "POST":

        # Instantiate the form with the data from the POST request
        form = CustomUserCreationForm(request.POST)
        # Check if the form is valid
        if form.is_valid():
            user = form.save(commit=False) # it saves the user to db but without comitting yet
            user.is_active = False # initially users are inactive for verification via email
            user.save() # Save the user object to the database

            # Generate token for account activation
            token = default_token_generator.make_token(user)
            # Encode user ID for the activation URL
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Get the current domain (for generating the activation link)
            domain = get_current_site(request).domain

            # Create the activation URL
            activation_url = f'http://{domain}/activate/{uid}/{token}/'
            # Prepare email content
            subject = 'Account Activation for Service Booking'

            # Plain-text version of the email
            text_content = f"""
            Hello, {user.username}!

            Thank you for registering on Service Booking.
            To activate your account, please click on the link below:
            {activation_url}

            If you did not register, please ignore this email.
            """

            # HTML version of the email (using a template)
            html_content = render_to_string('auth/activation_email.html', {
                'user': user,
                'activation_url': activation_url,
            })

            # Create the email object
            email = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            # Attach the HTML version of the email
            email.attach_alternative(html_content, "text/html")
            email.send()

            # Show success message to the user
            messages.success(request, "Registration successful! Please check your email to activate your account.")
            return redirect('home')
        else:
            # If the form is invalid, show an error message
            messages.error(request, "Error. Please check the form and try again.")
    else:
        # If the request is GET, show the registration form
        form = CustomUserCreationForm()

    # Render the registration template with the form
    return render(request, 'auth/register.html', {'form': form})



""" ACCOUNT ACTIVATION VIEW FUNCTION """
def activate(request, uidb64, token):
    try:
        # Decode the base64 encoded user ID
        uid = urlsafe_base64_decode(uidb64).decode('utf-8')
        # Retrieve the user by primary key (ID)
        user = get_user_model().objects.get(pk=uid)
        # Check if the token is valid for this user
        if default_token_generator.check_token(user, token):
            user.is_active = True  # Activate the user account
            user.save()
            messages.success(request, "Your account has been successfully activated!")
            return redirect('login')  # Redirect to login page
        else:
            # If token is invalid, show an error message
            messages.error(request, "Unable to activate your account. Please check the link.")
            return redirect('home')
        # Handle exceptions if decoding fails or user does not exist
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        messages.error(request, "Activation error.")
        return redirect('home')



""" LOGIN VIEW FUNCTION"""
def login_user(request):
    if request.method == "POST":
        # Retrieve username and password from the submitted form
        username = request.POST['username']
        password = request.POST['password']

        # Attempt to authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # If authentication is successful, log the user in
            login(request, user)
            messages.success(request, "You have successfully logged in!")

            # If the user is an admin (superuser)
            if user.is_superuser:
                # Redirect him to this page
                return redirect('manage_users')
            else:
                # For standart users redirect to homepage
                return redirect('home')

        # If authentication failed, show an error message
        else:
            messages.error(request, "Error: incorrect username or password.")

    # If the request method is not POST, or login fails, display the login page
    return render(request, 'auth/login.html')



""" LOGOUT VIEW FUNCTION"""
def logout_user(request):
    if request.method == 'POST':
        logout(request)  # Log the user out and clear the session
        return redirect('home')
    return redirect('home')



""" BOOKING PAGE VIEW FUNCTION """
@login_required
def booking_page(request):
    return render(request, "booking/booking_form.html") # Just rendering the template



""" CREATE BOOKING VIEW FUNCTION """
@csrf_exempt # Disable CSRF protection for this view (for API calls)
@login_required # disable to use this logic without being logged in
def create_booking(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            service_id = data.get("service_id")
            master_id = data.get("master_id")
            booking_date = data.get("date")
            booking_time = data.get("time")
            user = request.user # Get the currently logged-in user

            # Validate that all required fields are provided
            if not (service_id and master_id and booking_date and booking_time):
                return JsonResponse({"error": "All fields are required!"}, status=400)

            try:
                # Retrieve the Service and Master objects from the database
                service = Service.objects.get(id=service_id)
                master = Master.objects.get(id=master_id)
                salon = master.salon
            except (Service.DoesNotExist, Master.DoesNotExist):
                return JsonResponse({"error": "Service or master not found!"}, status=404)

            # Convert booking date and time from strings to Python objects
            booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
            booking_time = datetime.strptime(booking_time, "%H:%M").time()

            # Check if the master is already booked at the selected date and time
            if Booking.objects.filter(master=master, booking_date=booking_date, booking_time=booking_time).exists():
                return JsonResponse({"error": "This master is already booked at the selected time!"}, status=400)

            # Create the new booking
            booking = Booking.objects.create(
                user=user,
                service=service,
                master=master,
                booking_date=booking_date,
                booking_time=booking_time,
                status="pending"
            )

            # Prepare the booking confirmation email
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
            # send the confirmation email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            # Return a success response
            return JsonResponse({"message": "Booking successful, please check your email"}, status=201)

        # Handle JSON parsing errors
        except json.JSONDecodeError:
            return JsonResponse({"error": "Error in JSON format!"}, status=400)
    # If the request method is not POST, return an error
    return JsonResponse({"error": "Method not supported!"}, status=405)



""" CANCEL BOOKING VIEW FUNCTION """
@csrf_exempt
def cancel_booking_by_url(request, booking_id):
    if request.method == "DELETE":
        try:
            booking = Booking.objects.get(id=booking_id)

            now = datetime.now().date()
            if booking.booking_date < now:
                return JsonResponse({"success": False, "message": "Cannot cancel past booking."}, status=400)

            user_email = booking.user.email
            service_name = booking.service.name
            booking_date = booking.booking_date.strftime("%d.%m.%Y")
            booking_time = booking.booking_time.strftime("%H:%M")

            booking.delete()

            send_mail(
                "Booking Canceled",
                f"Your booking for {service_name} on {booking_date} at {booking_time} has been successfully canceled.",
                "muhammadkhongaybulloev17@gmail.com",
                [user_email],
                fail_silently=False,
            )

            return JsonResponse({"success": True})
        except Booking.DoesNotExist:
            return JsonResponse({"success": False, "message": "Booking not found."}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Method not allowed."}, status=405)

""" BOOKING DETAIL VIEW FUNCTION """
def booking_details(request, booking_id):
    try:
        # Try to find the booking with the given booking_id
        booking = Booking.objects.get(id=booking_id)

        #  Prepare the response data as a dictionary
        response_data = {
            "booking_id": booking.id,
            "user": booking.user.username,
            "date": booking.booking_date.strftime('%d %B %Y'), # Format date like '29 April 2025'
            "time": booking.booking_time.strftime('%H:%M'),
            "master_name": booking.master.name,
            "master_role": booking.master.role,
            "service": booking.service.name,
            "price": f"{booking.service.price} so’m",
            "salon": booking.master.salon.name,
            "location": booking.master.salon.location,
            "contact": booking.master.salon.contact_email
        }

        return JsonResponse(response_data) # Return the data as a JSON response

    except Booking.DoesNotExist:
        return JsonResponse({"error": "Booking not found!"}, status=404)


"""SERVICE LIST VIEW FUNCTION"""
def service_list(request):
    services = Service.objects.all()
    form = ServiceFilterForm(request.GET) # Initialize the filter form with GET parameters

    # If the form is valid, apply filters
    if form.is_valid():
        # Filter by category
        category = form.cleaned_data.get('category')
        if category:
            services = services.filter(category=category)

        # Filter by min price
        price_min = form.cleaned_data.get('price_min')
        if price_min:
            services = services.filter(price__gte=price_min)

        # Filter by max price
        price_max = form.cleaned_data.get('price_max')
        if price_max:
            services = services.filter(price__lte=price_max)

        # Filter by min duration
        duration_min = form.cleaned_data.get('duration_min')
        if duration_min:
            services = services.filter(duration__gte=duration_min)

        # Filter by max duration
        duration_max = form.cleaned_data.get('duration_max')
        if duration_max:
            services = services.filter(duration__lte=duration_max)

        # Sort the results if a sort option is provided
        sort_by = form.cleaned_data.get('sort_by')
        if sort_by:
            services = services.order_by(sort_by)

    # Render the HTML template with the filtered services and the form
    return render(request, 'service/service_list.html', {'services': services, 'form': form})



"""SERVICE DETAIL VIEW FUNCTION"""
def service_detail(request, service_id):
    # Try to get the Service object with the provided service_id. If it doesn't exist, return a 404 error.
    service = get_object_or_404(Service, id=service_id)
    return render(request, 'service/service_detail.html', {'service': service})



""" PROFILE VIEW FUNCTION """
@login_required
def profile(request):
    user = request.user # Get the current logged-in user

    # Try to fetch the user's profile, if it doesn't exist, create one
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user)

    # Fetch the user's booking history. Filter by status if provided in GET request.
    bookings = Booking.objects.filter(user=user)
    if 'status' in request.GET:
        # Filter bookings based on the 'status' parameter from the GET request
        bookings = bookings.filter(status=request.GET['status'])

    # Handle the profile update form (when POST request is made)
    if request.method == "POST":
        # Instantiate the form with the POST data and the existing profile instance
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            # Save the updated profile data if the form is valid
            form.save()
            messages.success(request, 'profile updated successfully!')
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    # Render the profile template and pass the necessary context
    return render(request, "profile/profile.html", {
        "user": user,
        "profile": profile,
        "form": form,
        "bookings": bookings
    })



""" UPDATE PROFILE VIEW FUNCTION """
@login_required
def update_profile(request):
    user = request.user
    if request.method == 'POST':
        # Initialize the form with POST data and the current user's data
        form = UserUpdateForm(request.POST, instance=user)
        # Check if the form data is valid
        if form.is_valid():
            form.save()
            # Redirect to the profile page after the update is successful
            return redirect('profile')
    else:
        # If the request is GET (or any other method), create the form with the user's current data
        form = UserUpdateForm(instance=user)

    # Render the 'update_profile.html' template and pass the form as context
    return render(request, 'profile/update_profile.html', {'form': form})



""" AVAILABLE SLOTS API VIEW FUNCTION """
@api_view(['GET'])
def available_slots(request):
    # Retrieve the service ID and the date from the query string
    service_id = request.GET.get('service_id')
    date_str = request.GET.get('date')

    # If either 'service_id' or 'date' is not provided, return an error response
    if not service_id or not date_str:
        return Response({"error": "service_id and date are required"}, status=400)

    try:
        # Attempt to convert the 'date' string to a date object using the expected format YYYY-MM-D
        date = datetime.strptime(date_str, "%Y-%m-%d").date()  # Convert string to date
    except ValueError:
        # If the date string doesn't match the expected format, return an error response
        return Response({"error": "Invalid date format. Please use YYYY-MM-DD."}, status=400)

    # Retrieve the service object based on the provided service ID
    service = Service.objects.get(id=service_id)
    duration = service.duration  # Get the duration of the service (i.e., the length of time each booking will take)

    start_time = datetime.strptime("09:00", "%H:%M")  # Start of working hours
    end_time = datetime.strptime("18:00", "%H:%M")  # End of working hours

    available_slots = []  # List to store available time slots
    current_time = start_time  # Initialize current time at the start of the workday

    # Iterate over the time range from start time to end time, checking each 30-minute slot
    while current_time + timedelta(minutes=duration) <= end_time:
        # Check if the current time slot is already booked for the given service and date
        if not Booking.objects.filter(
                service=service,
                booking_date=date,
                booking_time=current_time.time() # Compare the time part of current_time
        ).exists():
            # If the slot is not booked, add it to the available_slots list
            available_slots.append(current_time.strftime("%H:%M"))

        # Increment current time by 1 hour to check the next potential slot
        current_time += timedelta(minutes=60)  # Check every 30 minutes

    # Return the list of available slots as a response
    return Response({"available_slots": available_slots})



""" GET SERVICES API VIEW FUNCTION """
@api_view(['GET'])
def get_services(request):
    """ Get a list of all services """
    services = Service.objects.all()
    # Serialize the list of services into a format suitable for API response
    serializer = ServiceSerializer(services, many=True)
    # Return the serialized data in the response
    return Response(serializer.data)



""" GET MASTERS API VIEW FUNCTION """
def get_masters(request):
    service_id = request.GET.get("service_id")

    # Check if 'service_id' is provided in the request; if not, return an error
    if not service_id:
        return JsonResponse({"error": "service_id is required"}, status=400)

    # Filter the masters by 'service_id' and select only 'id' and 'name' fields
    masters = Master.objects.filter(service_id=service_id).values("id", "name")

    # Return the list of masters in JSON format
    return JsonResponse(list(masters), safe=False)



""" TOP MASTERS VIEW FUNCTION """
def top_masters(request):
    # Query to get the top 5 masters, ordered by their average rating
    masters = (
        Master.objects.annotate(avg_rating=Avg("reviews__rating")) # Annotate each master with their average rating from reviews
        .order_by("-avg_rating")[:5] # Order by average rating in descending order and limit to top 5 masters
    )

    # Prepare the data for the response, including master details and their ratings
    data = [
        {
            "id": master.id,
            "name": master.name,
            "role": master.role,
            "rating": round(master.avg_rating, 1) if master.avg_rating else "No reviews",
            "image": master.image.url if master.image else None,
            "service": master.service.name,
        }
        for master in masters # Loop over the masters to construct the response data
    ]

    # Return the data as a JSON response
    return JsonResponse(data, safe=False)


""" SALON DETAIL VIEW FUNCTION """
def salon_detail(request, salon_id):
    salon = Salon.objects.get(id=salon_id) #get all salons by id
    services = Service.objects.all() # retrieve all service objects
    # render this page
    return render(request, 'salon/salon_detail.html', {'salon': salon,'service':services})



""" MASTERS VIEW FUNCTION """
def masters(request):
    masters = Master.objects.all() # all masters retrieved

    # context for template
    context = {"masters" : masters}
    # rendering the provided context to that page
    return render(request,"master/masters.html",context)



""" SALONS VIEW FUNCTION """
def salons(request):
    salons = Salon.objects.all() # salon objects retrieved
    context = {"salons" : salons}
    return render(request,"salon/salons.html",context)