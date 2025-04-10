from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from users.models import Booking

class Command(BaseCommand):
    help = "Sends booking reminders"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        today = now.date()

        upcoming_bookings = Booking.objects.filter(booking_date=today)

        for booking in upcoming_bookings:
            email_subject = "⏳ Booking Reminder"
            email_body = (
                f"Hello, {booking.user.username}! This is a reminder that you have an appointment "
                f"for {booking.service.name} on {booking.booking_date} at {booking.booking_time}. "
                f"Please be on time! 😊"
            )

            send_mail(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,  # Sender
                [booking.user.email],         # Recipient
                fail_silently=False,
            )

        self.stdout.write(self.style.SUCCESS("Reminders sent successfully!"))
