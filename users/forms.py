import re
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django import forms
from .models import Service, Profile, Review
from .models import CustomUser, Booking


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number')

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['username'].widget.attrs.update({'class': 'form-control'})
            self.fields['email'].widget.attrs.update({'class': 'form-control'})
            self.fields['password1'].widget.attrs.update({'class': 'form-control'})
            self.fields['password2'].widget.attrs.update({'class': 'form-control'})

        # Валидация email
        def clean_email(self):
            email = self.cleaned_data.get('email')
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError("Этот email уже используется. Пожалуйста, выберите другой.")
            return email

        def clean_phone_number(self):
            phone_number = self.cleaned_data.get('phone_number')
            if CustomUser.objects.filter(phone_number=phone_number).exists():
                raise ValidationError('Этот номер телефона уже зарегистрирован.')
            return phone_number

User = get_user_model()
class ProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label="Username")

    class Meta:
        model = Profile
        fields = ['username']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['username'].initial = user.username

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.username = self.cleaned_data['username']
        if commit:
            user.save()
            profile.save()
        return profile


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'date_of_birth', 'address', 'bio']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 3}),
        }


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['service', 'booking_date']

    def clean_booking_date(self):
        """ check if slot is avalibale"""
        service = self.cleaned_data.get('service')
        booking_date = self.cleaned_data.get('booking_date')

        if Booking.objects.filter(service=service, booking_date=booking_date).exists():
            raise ValidationError("This slot is already booked!")

        return booking_date


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


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')

        # Phone validation
        pattern = re.compile(r'^\+998\d{9}$')  # E.g for Uzb
        if not pattern.match(phone_number):
            raise forms.ValidationError('Incorrect phone format. Please use format: +998xxxxxxxxx')

        return phone_number


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i}⭐") for i in range(1, 6)]),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Leave a feedback..."}),
        }

