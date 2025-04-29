from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Service, Profile, Review, Promotion, CustomUser, Booking
from django import forms

# --- Custom user creation form inheriting from Django's built-in UserCreationForm ---
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser  # Using the custom user model
        fields = ('full_name', 'username', 'email', 'phone_number')  # Fields to include in the form

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adding Bootstrap classes to form fields for better UI styling
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['full_name'].widget.attrs.update({'class': 'form-control'})

    # Email field validation to prevent duplicate emails
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email address is already in use. Please choose another one.")
        return email

    # Phone number field validation to prevent duplicate phone numbers
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise ValidationError('This phone number is already registered. Please choose another one.')
        return phone_number


# Reference to the custom user model
User = get_user_model()

# --- Form to update the user's profile (username only) ---
class ProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label="Username")

    class Meta:
        model = Profile
        fields = ['username']  # Only allows updating the username

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Pre-filling the username field with the current username
        if user:
            self.fields['username'].initial = user.username

    def save(self, commit=True):
        profile = super().save(commit=False)
        # Save the new username in the related user object
        user = profile.user
        user.username = self.cleaned_data['username']
        if commit:
            user.save()
            profile.save()
        return profile


# --- Simple form to update just the username ---
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username']


# --- Form to update profile details like full name, birthdate, etc. ---
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'date_of_birth', 'address', 'bio']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),  # Date picker input
            'bio': forms.Textarea(attrs={'rows': 3}),  # Text area for bio
        }


# --- Booking form to allow users to choose a service and date ---
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['service', 'booking_date']

    # Custom validation to check if the selected time slot is already booked
    def clean_booking_date(self):
        service = self.cleaned_data.get('service')
        booking_date = self.cleaned_data.get('booking_date')

        if Booking.objects.filter(service=service, booking_date=booking_date).exists():
            raise ValidationError("This slot is already booked!")

        return booking_date


# --- Service filter form for searching or filtering services ---
class ServiceFilterForm(forms.Form):
    CATEGORY_CHOICES = Service.CATEGORY_CHOICES
    category = forms.ChoiceField(choices=[('', 'All categories')] + CATEGORY_CHOICES, required=False)
    price_min = forms.DecimalField(min_value=0, required=False)
    price_max = forms.DecimalField(min_value=0, required=False)
    duration_min = forms.IntegerField(min_value=0, required=False)
    duration_max = forms.IntegerField(min_value=0, required=False)
    sort_by = forms.ChoiceField(choices=[
        ('', 'Do not sort'),
        ('price', 'Price'),
        ('duration', 'Duration'),
        ('name', 'Name')
    ], required=False)


# --- Form for submitting a review with rating and comment ---
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i}⭐") for i in range(1, 6)]),  # Dropdown for star rating
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Leave a feedback..."}),
        }


# --- Form for creating or editing promotions ---
class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = '__all__'  # Include all fields from the Promotion model
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    # Additional validation logic for promotion dates
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Ensure start date is before end date
        if start_date and end_date and start_date > end_date:
            raise ValidationError("End date must be after start date")

        # Ensure end date is not in the past
        if end_date and end_date < timezone.now().date():
            raise ValidationError("End date cannot be in the past")

        return cleaned_data
