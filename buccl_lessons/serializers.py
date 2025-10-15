from rest_framework import serializers
from .models import LessonProduct, InstructorSchedule, Ticket, SessionReservation, PracticeSession, PracticeReservation


class LessonProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProduct
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class InstructorScheduleSerializer(serializers.ModelSerializer):
    lesson_product_title = serializers.CharField(source='lesson_product.title', read_only=True)
    instructor_name = serializers.CharField(source='instructor.user_id', read_only=True)
    available_spots = serializers.IntegerField(read_only=True)
    sport_name = serializers.CharField(source='lesson_product.sport.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    waiting_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InstructorSchedule
        fields = [
            'id', 'lesson_product', 'lesson_product_title', 'instructor', 'instructor_name',
            'date', 'start_time', 'end_time', 'location', 'location_name', 'capacity', 'current_bookings',
            'available_spots', 'status', 'created_at', 'updated_at', 'sport_name',
            'waiting_count'
        ]
        read_only_fields = ('id', 'current_bookings', 'available_spots', 'created_at', 'updated_at',
                          'sport_name', 'waiting_count', 'location_name')
    
    def get_waiting_count(self, obj):
        # Count reservations with waiting status for this schedule
        return SessionReservation.objects.filter(
            schedule=obj,
            status='RESERVED',
            is_waiting=True
        ).count()


class TicketSerializer(serializers.ModelSerializer):
    lesson_product_title = serializers.CharField(source='lesson_product.title', read_only=True)
    user_id = serializers.CharField(source='user.user_id', read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('id', 'sessions_used', 'status', 'created_at', 'updated_at')


class SessionReservationSerializer(serializers.ModelSerializer):
    schedule_info = InstructorScheduleSerializer(source='schedule', read_only=True)

    class Meta:
        model = SessionReservation
        fields = [
            'id', 'ticket', 'schedule', 'schedule_info', 'day_order', 'is_theory',
            'status', 'created_at', 'cancelled_at'
        ]
        read_only_fields = ('id', 'status', 'created_at', 'cancelled_at')


# ---------------- Practice ----------------


class PracticeSessionSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.user_id', read_only=True)
    waiting_count = serializers.IntegerField(read_only=True)
    sport_name = serializers.CharField(source='sport.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = PracticeSession
        fields = [
            'id', 'title', 'sport', 'sport_name', 'instructor', 'instructor_name', 'date',
            'start_time', 'end_time', 'location', 'location_name', 'capacity', 'current_bookings',
            'waiting_count', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'current_bookings', 'waiting_count', 'created_at', 'updated_at',
                           'sport_name', 'location_name')


class PracticeReservationSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source='user.user_id', read_only=True)
    session_title = serializers.CharField(source='practice_session.title', read_only=True)

    class Meta:
        model = PracticeReservation
        fields = [
            'id', 'practice_session', 'session_title', 'user', 'user_id',
            'status', 'is_waiting', 'queue_position', 'created_at', 'cancelled_at'
        ]
        read_only_fields = ('id', 'status', 'is_waiting', 'queue_position', 'created_at', 'cancelled_at') 