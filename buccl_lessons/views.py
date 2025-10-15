from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, F

from .models import (
    LessonProduct, InstructorSchedule, Ticket, SessionReservation,
    PracticeSession, PracticeReservation
)
from .serializers import (
    LessonProductSerializer, InstructorScheduleSerializer, TicketSerializer,
    SessionReservationSerializer, PracticeSessionSerializer, PracticeReservationSerializer
)
from buccl_main.models import Sport


class LessonProductViewSet(viewsets.ModelViewSet):
    queryset = LessonProduct.objects.all()
    serializer_class = LessonProductSerializer


class InstructorScheduleViewSet(viewsets.ModelViewSet):
    queryset = InstructorSchedule.objects.all()
    serializer_class = InstructorScheduleSerializer

    def get_queryset(self):
        # ✅ 최적화: 관련된 모든 데이터를 한 번에 가져오기
        queryset = InstructorSchedule.objects.select_related(
            'lesson_product',           # 레슨 상품 정보
            'lesson_product__sport',    # 스포츠 정보  
            'instructor',               # 강사 정보
            'location'                  # 장소 정보
        ).prefetch_related(
            # 예약 정보도 미리 가져오기 (대기자 수 계산용)
            'reservations'
        )
        
        # 특정 날짜로 필터링 (정확한 날짜 하나)
        date = self.request.query_params.get('date', None)
        if date:
            queryset = queryset.filter(date=date)
        else:
            # 기존 date_from, date_to 필터링 로직
            date_from = self.request.query_params.get('date_from', None)
            if date_from:
                queryset = queryset.filter(date__gte=date_from)
                
            date_to = self.request.query_params.get('date_to', None)
            if date_to:
                queryset = queryset.filter(date__lte=date_to)
        
        # Filter by sport
        sport_id = self.request.query_params.get('sport', None)
        if sport_id:
            queryset = queryset.filter(lesson_product__sport_id=sport_id)
        
        # Filter by instructor
        instructor_id = self.request.query_params.get('instructor', None)
        if instructor_id:
            queryset = queryset.filter(instructor_id=instructor_id)
            
        # Filter by location
        location = self.request.query_params.get('location', None)
        if location:
            # location param can be ID or partial name
            if location.isdigit():
                queryset = queryset.filter(location_id=location)
            else:
                queryset = queryset.filter(location__name__icontains=location)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def reservations(self, request, pk=None):
        schedule = self.get_object()
        reservations = schedule.reservations.all()
        serializer = SessionReservationSerializer(reservations, many=True)
        return Response(serializer.data)


class TicketViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # ✅ 최적화: 관련 데이터를 한 번에 가져오기
            return Ticket.objects.filter(user=user).select_related(
                'lesson_product',        # 레슨 상품 정보
                'lesson_product__sport', # 스포츠 정보
                'order'                  # 주문 정보
            )
        return Ticket.objects.none()


class SessionReservationViewSet(viewsets.ModelViewSet):
    queryset = SessionReservation.objects.all()
    serializer_class = SessionReservationSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # ✅ 최적화: 모든 관련 데이터를 한 번에 가져오기
            return SessionReservation.objects.filter(
                ticket__user=user
            ).select_related(
                'ticket',                              # 티켓 정보
                'ticket__lesson_product',              # 레슨 상품 정보
                'schedule',                            # 스케줄 정보
                'schedule__instructor',                # 강사 정보
                'schedule__lesson_product',            # 스케줄의 레슨 정보
                'schedule__lesson_product__sport',     # 스포츠 정보
                'schedule__location'                   # 장소 정보
            )
        return SessionReservation.objects.none()


class ApplySessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, schedule_id):
        schedule = get_object_or_404(InstructorSchedule, id=schedule_id)
        user = request.user
        
        # Check if this is a practice session
        is_free_practice = request.query_params.get('is_free_practice', 'false').lower() == 'true'
        
        if is_free_practice:
            # Handle practice session reservation
            practice_session = get_object_or_404(PracticeSession, id=schedule_id)
            
            # Check if user already has a reservation for this session
            existing_reservation = PracticeReservation.objects.filter(
                user=user,
                practice_session=practice_session,
                status='RESERVED'
            ).first()
            
            if existing_reservation:
                return Response(
                    {"error": "You already have a reservation for this practice session"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if there are available spots
            is_waiting = practice_session.current_bookings >= practice_session.capacity
            
            # Create reservation
            with transaction.atomic():
                if is_waiting:
                    # Add to waiting list
                    last_position = PracticeReservation.objects.filter(
                        practice_session=practice_session,
                        is_waiting=True
                    ).order_by('-queue_position').first()
                    
                    queue_position = 1
                    if last_position:
                        queue_position = last_position.queue_position + 1
                    
                    reservation = PracticeReservation.objects.create(
                        user=user,
                        practice_session=practice_session,
                        is_waiting=True,
                        queue_position=queue_position
                    )
                    
                    return Response({
                        "message": "Added to waiting list",
                        "queue_position": queue_position,
                        "reservation_id": reservation.id
                    }, status=status.HTTP_201_CREATED)
                else:
                    # Regular reservation
                    reservation = PracticeReservation.objects.create(
                        user=user,
                        practice_session=practice_session,
                        is_waiting=False
                    )
                    
                    # Update current bookings
                    practice_session.current_bookings = F('current_bookings') + 1
                    practice_session.save(update_fields=['current_bookings'])
                    
                    return Response({
                        "message": "Reservation successful",
                        "reservation_id": reservation.id
                    }, status=status.HTTP_201_CREATED)
        else:
            # Handle regular lesson reservation
            # Check if user has an available ticket
            ticket = Ticket.objects.filter(user=user, status='ACTIVE').first()
            
            if not ticket:
                return Response(
                    {"error": "No active ticket available for reservation"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user already has a reservation for this schedule
            existing_reservation = SessionReservation.objects.filter(
                ticket__user=user,
                schedule=schedule,
                status='RESERVED'
            ).first()
            
            if existing_reservation:
                return Response(
                    {"error": "You already have a reservation for this session"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if there are available spots
            if schedule.current_bookings >= schedule.capacity:
                # Add to waiting list instead of rejecting
                # Find the highest queue position in waiting list
                last_position = SessionReservation.objects.filter(
                    schedule=schedule,
                    is_waiting=True
                ).order_by('-queue_position').first()
                
                queue_position = 1
                if last_position:
                    queue_position = last_position.queue_position + 1
                
                # Create waiting reservation
                reservation = SessionReservation.objects.create(
                    ticket=ticket,
                    schedule=schedule,
                    is_waiting=True,
                    queue_position=queue_position,
                    day_order=request.data.get('day_order'),
                    is_theory=request.data.get('is_theory', False)
                )
                
                return Response({
                    "message": "Added to waiting list",
                    "queue_position": queue_position,
                    "reservation_id": reservation.id
                }, status=status.HTTP_201_CREATED)
            
            # Check if this is a theory session 
            is_theory = request.data.get('is_theory', False)
            
            # For non-theory sessions, check sequential day order
            day_order = None
            if not is_theory:
                day_order = request.data.get('day_order')
                
                if day_order is None:
                    return Response({
                        "error": "Day order is required for non-theory sessions"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # For sequential reservations, verify the user has all previous days reserved
                if day_order > 1:
                    # Check all previous day orders are already reserved
                    for prev_day in range(1, day_order):
                        has_prev_day = SessionReservation.objects.filter(
                            ticket__user=user,
                            status='RESERVED',
                            day_order=prev_day,
                            is_theory=False
                        ).exists()
                        
                        if not has_prev_day:
                            return Response({
                                "error": f"You must first reserve Day {prev_day} before reserving Day {day_order}"
                            }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create the reservation
            with transaction.atomic():
                reservation = SessionReservation.objects.create(
                    ticket=ticket,
                    schedule=schedule,
                    day_order=day_order,
                    is_theory=is_theory
                )
                
                # Update current bookings
                schedule.current_bookings = F('current_bookings') + 1
                schedule.save(update_fields=['current_bookings'])
                
                return Response({
                    "message": "Reservation successful",
                    "reservation_id": reservation.id
                }, status=status.HTTP_201_CREATED)


class CancelSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def delete(self, request, schedule_id):
        user = request.user
        
        # Check if this is a practice session
        is_free_practice = request.query_params.get('is_free_practice', 'false').lower() == 'true'
        
        if is_free_practice:
            # Handle practice session cancellation
            practice_session = get_object_or_404(PracticeSession, id=schedule_id)
            
            # Find the user's reservation
            reservation = get_object_or_404(
                PracticeReservation,
                user=user,
                practice_session=practice_session,
                status='RESERVED'
            )
            
            with transaction.atomic():
                # Update reservation status
                reservation.status = 'CANCELLED'
                reservation.save(update_fields=['status'])
                
                if not reservation.is_waiting:
                    # Update current bookings for regular reservation
                    practice_session.current_bookings = F('current_bookings') - 1
                    practice_session.save(update_fields=['current_bookings'])
                    
                    # Check if there's someone on the waiting list to move up
                    waiting_reservation = PracticeReservation.objects.filter(
                        practice_session=practice_session,
                        is_waiting=True,
                        status='RESERVED'
                    ).order_by('queue_position').first()
                    
                    if waiting_reservation:
                        # Move the first person from waiting list to confirmed
                        waiting_reservation.is_waiting = False
                        waiting_reservation.queue_position = None
                        waiting_reservation.save(update_fields=['is_waiting', 'queue_position'])
                        
                        # Update queue positions for remaining waiting list
                        PracticeReservation.objects.filter(
                            practice_session=practice_session,
                            is_waiting=True,
                            status='RESERVED',
                            queue_position__gt=1
                        ).update(queue_position=F('queue_position') - 1)
                
                return Response({"message": "Reservation cancelled successfully"}, status=status.HTTP_200_OK)
        else:
            # Handle regular lesson cancellation
            schedule = get_object_or_404(InstructorSchedule, id=schedule_id)
            
            # Find the user's reservation
            reservation = get_object_or_404(
                SessionReservation,
                ticket__user=user,
                schedule=schedule,
                status='RESERVED'
            )
            
            with transaction.atomic():
                # Update reservation status
                reservation.status = 'CANCELLED'
                reservation.save(update_fields=['status'])
                
                # Update current bookings
                schedule.current_bookings = F('current_bookings') - 1
                schedule.save(update_fields=['current_bookings'])
                
                return Response({"message": "Reservation cancelled successfully"}, status=status.HTTP_200_OK)


class PracticeSessionViewSet(viewsets.ModelViewSet):
    queryset = PracticeSession.objects.all()
    serializer_class = PracticeSessionSerializer
    
    def get_queryset(self):
        # ✅ 최적화: 관련된 모든 데이터를 한 번에 가져오기
        queryset = PracticeSession.objects.select_related(
            'instructor',                    # 강사 정보
            'sport',                        # 스포츠 정보
            'location',                     # 장소 정보
            'base_schedule',                # 기본 스케줄 정보 (있다면)
            'base_schedule__lesson_product' # 레슨 상품 정보 (brand_name용)
        ).prefetch_related(
            'reservations'                  # 예약 정보 (대기자 수 계산용)
        )
        
        # 특정 날짜로 필터링 (정확한 날짜 하나)
        date = self.request.query_params.get('date', None)
        if date:
            queryset = queryset.filter(date=date)
        else:
            # 기존 date_from, date_to 필터링 로직
            date_from = self.request.query_params.get('date_from', None)
            if date_from:
                queryset = queryset.filter(date__gte=date_from)
                
            date_to = self.request.query_params.get('date_to', None)
            if date_to:
                queryset = queryset.filter(date__lte=date_to)
        
        # Filter by sport
        sport_id = self.request.query_params.get('sport', None)
        if sport_id:
            queryset = queryset.filter(sport_id=sport_id)
        
        # Filter by location
        location_id = self.request.query_params.get('location', None)
        if location_id:
            queryset = queryset.filter(location_id=location_id)
            
        # Filter by instructor
        instructor_id = self.request.query_params.get('instructor', None)
        if instructor_id:
            queryset = queryset.filter(instructor_id=instructor_id)
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def waiting_position(self, request, pk=None):
        """Get waiting position for current user if they're in the waiting list"""
        practice_session = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        reservation = PracticeReservation.objects.filter(
            practice_session=practice_session,
            user=user,
            status='RESERVED',
            is_waiting=True
        ).first()
        
        if not reservation:
            return Response({"error": "You are not in the waiting list for this session"}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "queue_position": reservation.queue_position,
            "total_waiting": practice_session.waiting_count()
        })


class PracticeReservationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PracticeReservation.objects.all()
    serializer_class = PracticeReservationSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # ✅ 최적화: 관련 데이터를 한 번에 가져오기
            return PracticeReservation.objects.filter(user=user).select_related(
                'practice_session',            # 연습 세션 정보
                'practice_session__instructor', # 강사 정보
                'practice_session__sport',     # 스포츠 정보
                'practice_session__location'   # 장소 정보
            )
        return PracticeReservation.objects.none()


class MyReservationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # ✅ 더 완벽한 최적화: 시리얼라이저에서 사용하는 모든 관련 데이터 미리 로드
        session_reservations = SessionReservation.objects.filter(
            ticket__user=user,
            status='RESERVED'
        ).select_related(
            'schedule__instructor',
            'schedule__lesson_product__sport',
            'schedule__location',
            'ticket__lesson_product'
        )
        
        # Get all active practice reservations
        practice_reservations = PracticeReservation.objects.filter(
            user=user,
            status='RESERVED'
        ).select_related(
            'practice_session__instructor',
            'practice_session__sport',
            'practice_session__location'
        )
        
        result = {
            "lessons": SessionReservationSerializer(session_reservations, many=True).data,
            "practices": PracticeReservationSerializer(practice_reservations, many=True).data
        }
        
        return Response(result) 