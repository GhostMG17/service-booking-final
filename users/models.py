import datetime
import phonenumbers
from django import forms
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("user", "User"),
        ("owner", "Owner"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    is_owner = models.BooleanField(default=False)
    email = models.EmailField(unique=True, blank=False)
    is_active = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    password = models.CharField(max_length=100)

    def clean(self):
        if self.phone_number:
            try:
                parsed_number = phonenumbers.parse(self.phone_number, 'UZ')
                if not phonenumbers.is_valid_number(parsed_number):
                    raise ValidationError('Invalid phone number. Please enter a correct number.')
            except phonenumbers.phonenumberutil.NumberParseException:
                raise ValidationError('Invalid phone number format.')

        super().clean()


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    #profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Service(models.Model):
    CATEGORY_CHOICES = [
        ('hair', 'Haircut Services'),
        ('nail', 'Manicure'),
        ('massage', 'Massage'),
        # Add other categories as necessary
    ]

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    duration = models.IntegerField()  # Duration in minutes
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='hair')
    description = models.TextField()
    availability = models.BooleanField(default=True)
    image = models.ImageField(upload_to='services/', blank=True, null=True)

    def __str__(self):
        return self.name


class Salon(models.Model):
    name = models.CharField(max_length=255)
    location = models.TextField()
    contact_email = models.EmailField()


class Master(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, default="Barber")
    email = models.EmailField(unique=True, blank=False, default="default@example.com")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="masters")
    salon = models.ForeignKey(Salon, on_delete=models.SET_NULL, null=True, blank=True, related_name="masters")

    def __str__(self):
        return f"{self.name} ({self.service.name})"

    def average_rating(self):
        return self.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.0

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.user.username} - {self.service.name} on {self.date}"

    def formatted_date(self):
        return self.date.strftime("%d.%m.%Y %H:%M")


class ServiceFilterForm(forms.Form):
    category = forms.ChoiceField(choices=[('', 'All Categories')] + Service.CATEGORY_CHOICES)
    price_min = forms.DecimalField(label='Minimum Price', required=False,)
    price_max = forms.DecimalField(label='Maximum Price', required=False)
    duration_min = forms.IntegerField(label='Minimum Duration', required=False)
    duration_max = forms.IntegerField(label='Maximum Duration', required=False)
    sort_by = forms.ChoiceField(choices=[
        ('price', 'By Price'),
        ('duration', 'By Duration'),
        ('name', 'By Name')
    ], required=False)


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
    ]
    master = models.ForeignKey(Master, on_delete=models.CASCADE, null=True, blank=True)  # New field
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="bookings")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="bookings")
    booking_date = models.DateField()  # Separate booking date
    booking_time = models.TimeField(default=datetime.time(12, 0))  # Separate booking time
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('master', 'booking_date', 'booking_time')  # Unique booking by date and time

    def clean(self):
        """ Check if the time is already taken based on service duration """
        from datetime import datetime, timedelta

        # Service duration
        duration = self.service.duration

        # Start and end time of booking
        start_time = datetime.combine(self.booking_date, self.booking_time)
        end_time = start_time + timedelta(minutes=duration)

        # Check for overlapping bookings
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


class Review(models.Model):
    booking = models.OneToOneField("Booking", on_delete=models.CASCADE, related_name="review")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Client
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="reviews", null=True, blank=True)
    master = models.ForeignKey(Master, on_delete=models.CASCADE, related_name="reviews", null=True, blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)  # Make it optional
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review from {self.user.username} - {self.rating}⭐"

    class Meta:
        ordering = ["-created_at"]
