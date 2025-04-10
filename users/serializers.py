from rest_framework import serializers
from datetime import datetime, timedelta
from .models import Booking, Service

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

    def validate(self, data):
        """ Check if the time slot is already booked """
        service = data['service']
        booking_date = data['booking_date']
        booking_time = data['booking_time']

        # Get service duration
        duration = service.duration
        start_time = datetime.combine(booking_date, booking_time)
        end_time = start_time + timedelta(minutes=duration)

        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            service=service,
            booking_date=booking_date,
        ).exclude(id=self.instance.id if self.instance else None).filter(
            booking_time__gte=start_time.time(),
            booking_time__lt=end_time.time()
        )

        if overlapping_bookings.exists():
            raise serializers.ValidationError("This time slot is already booked!")

        return data


class AvailableSlotsSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()
    date = serializers.DateField()


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'duration']  # Specify required fields
