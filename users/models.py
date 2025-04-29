import datetime
from decimal import Decimal
from django.utils import timezone
import phonenumbers
from django import forms
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg


# Custom user model with extended fields and validation
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("user", "User"),
        ("owner", "Owner"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    is_owner = models.BooleanField(default=False)
    email = models.EmailField(unique=True, blank=False)
    is_active = models.BooleanField(default=False)  # Email confirmation can be used to activate
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    password = models.CharField(max_length=100)
    full_name = models.CharField(max_length=255, blank=True)

    def clean(self):
        # Phone number validation using 'phonenumbers' library for Uzbekistan
        if self.phone_number:
            try:
                parsed_number = phonenumbers.parse(self.phone_number, 'UZ')
                if not phonenumbers.is_valid_number(parsed_number):
                    raise ValidationError('Invalid phone number.')
            except phonenumbers.phonenumberutil.NumberParseException:
                raise ValidationError('Incorrect phone number format.')

        super().clean()

    def save(self, *args, **kwargs):
        # Automatically fill full_name if first and last names are available
        if not self.full_name and self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
        super().save(*args, **kwargs)


# User profile model (extra info linked to CustomUser)
class Profile(models.Model):
    # This field creates a one-to-one relationship between the Profile model and the CustomUser model.
    # each user will have exactly one profile, and each profile is linked to one user.
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Model representing a Salon or service location
class Salon(models.Model):
    name = models.CharField(max_length=255)
    location = models.TextField()
    contact_email = models.EmailField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)

    def __str__(self):
        return self.name


# Service that can be booked by users
class Service(models.Model):
    CATEGORY_CHOICES = [
        ('hair', 'Haircut Services'),
        ('botox', 'Cosmetology Services'),
        ('autoservice', 'Autoservice'),
    ]

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    duration = models.IntegerField()  # Service duration in minutes
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='hair')
    description = models.TextField()
    availability = models.BooleanField(default=True)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    # This field creates a foreign key relationship between this model and the Salon model.
    # allows many services to be linked to one salon (many-to-one relationship).
    salon = models.ForeignKey(Salon, related_name='services', on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.name


# Master member who provides a service
class Master(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, default="Barber")
    email = models.EmailField(unique=True, blank=False, default="default@example.com")
    # This field creates a foreign key relationship between this model and the Service model.
    # allows many masters to be linked to one service (many-to-one relationship).
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="master")
    salon = models.ForeignKey(Salon, on_delete=models.SET_NULL, null=True, blank=True, related_name="master")
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    experience = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))  # Years of experience

    def __str__(self):
        return f"{self.name} ({self.service.name})"

    def average_rating(self):
        # Calculates average review rating for this master
        return self.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.0

    def appointment_count(self):
        # Counts how many bookings this master has
        return self.bookings.count()

    def experience_display(self):
        # Nicely format experience (e.g. 2 instead of 2.00)
        if self.experience % 1 == 0:
            return str(int(self.experience))
        return str(self.experience)


# Order history for the user (not directly linked to booking time)
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)  # Automatically sets current timestamp
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.user.username} - {self.service.name} on {self.date}"

    def formatted_date(self):
        return self.date.strftime("%d.%m.%Y %H:%M")


# Form used to filter services on the frontend
class ServiceFilterForm(forms.Form):
    category = forms.ChoiceField(choices=[('', 'All Categories')] + Service.CATEGORY_CHOICES)
    price_min = forms.DecimalField(label='Minimum Price', required=False)
    price_max = forms.DecimalField(label='Maximum Price', required=False)
    duration_min = forms.IntegerField(label='Minimum Duration', required=False)
    duration_max = forms.IntegerField(label='Maximum Duration', required=False)
    sort_by = forms.ChoiceField(choices=[
        ('price', 'By Price'),
        ('duration', 'By Duration'),
        ('name', 'By Name')
    ], required=False)


# Booking model represents scheduled appointment between user and master
class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
    ]
    # allows many Bookings to be linked to one master (many-to-one relationship).
    master = models.ForeignKey(Master, on_delete=models.CASCADE, null=True, blank=True, related_name='bookings')
    # allows many Bookings to be linked to one user (many-to-one relationship).
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="bookings")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="bookings")
    booking_date = models.DateField()  # Selected date
    booking_time = models.TimeField(default=datetime.time(12, 0))  # Selected time
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('master', 'booking_date', 'booking_time')  # Prevent double booking

    def clean(self):
        # Check if the selected time overlaps with other bookings for the same service and day
        from datetime import datetime, timedelta
        duration = self.service.duration
        start_time = datetime.combine(self.booking_date, self.booking_time)
        end_time = start_time + timedelta(minutes=duration)

        overlapping_bookings = Booking.objects.filter(
            service=self.service,
            booking_date=self.booking_date,
        ).exclude(id=self.id).filter(
            booking_time__gte=start_time.time(),
            booking_time__lt=end_time.time()
        )

        if overlapping_bookings.exists():
            raise ValidationError("This time slot is already taken!")

    def __str__(self):
        return f"{self.service.name} - {self.booking_date} {self.booking_time} - {self.status}"


# User review after booking is completed
class Review(models.Model):
    booking = models.OneToOneField("Booking", on_delete=models.CASCADE, related_name="review")
    # allows many Review to be linked to one user (many-to-one relationship).
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # allows many Review to be linked to one Service (many-to-one relationship).
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="reviews", null=True, blank=True)
    # allows many Review to be linked to one Master (many-to-one relationship).
    master = models.ForeignKey(Master, on_delete=models.CASCADE, related_name="reviews", null=True, blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 to 5 stars
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review from {self.user.username} - {self.rating}⭐"

    class Meta:
        ordering = ["-created_at"]  # Latest reviews come first


# Promotional offers related to services
class Promotion(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    discount_percent = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    # allows many Promotion to be linked to one Service (many-to-one relationship).
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="promotions", null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.discount_percent}%)"

    @property
    def is_upcoming(self):
        return self.start_date > timezone.now().date()

    @property
    def is_active_now(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    @property
    def days_remaining(self):
        # Days left until promotion ends
        if not self.is_active:
            return 0
        return (self.end_date - timezone.now().date()).days

    @property
    def days_until_start(self):
        # Days until promotion becomes active
        if not self.is_upcoming:
            return 0
        return (self.start_date - timezone.now().date()).days
