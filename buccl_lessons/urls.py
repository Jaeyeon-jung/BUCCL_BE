from django.urls import path
from .views import (
    LessonProductViewSet, InstructorScheduleViewSet,
    TicketViewSet, SessionReservationViewSet,
    ApplySessionView, CancelSessionView,
    PracticeSessionViewSet, PracticeReservationViewSet, MyReservationsView
)

# Helper to map ViewSet actions to explicit urls (like buccl_main style)
lesson_product_list = LessonProductViewSet.as_view({'get': 'list', 'post': 'create'})
lesson_product_detail = LessonProductViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

schedule_list = InstructorScheduleViewSet.as_view({'get': 'list', 'post': 'create'})
schedule_detail = InstructorScheduleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
# custom reservations action
schedule_reservations = InstructorScheduleViewSet.as_view({'get': 'reservations'})

# Tickets (read-only)
ticket_list = TicketViewSet.as_view({'get': 'list'})
ticket_detail = TicketViewSet.as_view({'get': 'retrieve'})

# SessionReservation
reservation_list = SessionReservationViewSet.as_view({'get': 'list', 'post': 'create'})
reservation_detail = SessionReservationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

# PracticeSession
practice_list = PracticeSessionViewSet.as_view({'get': 'list', 'post': 'create'})
practice_detail = PracticeSessionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
practice_waiting = PracticeSessionViewSet.as_view({'get': 'waiting_position'})

# PracticeReservation
practice_reservation_list = PracticeReservationViewSet.as_view({'get': 'list'})
practice_reservation_detail = PracticeReservationViewSet.as_view({'get': 'retrieve'})

app_name = 'buccl_lessons'
urlpatterns = [
    # LessonProduct endpoints
    path('api/v1/lesson-products/', lesson_product_list, name='lessonproduct-list'),
    path('api/v1/lesson-products/<int:pk>/', lesson_product_detail, name='lessonproduct-detail'),

    # InstructorSchedule endpoints
    path('api/v1/instructor-schedules/', schedule_list, name='instructorschedule-list'),
    path('api/v1/instructor-schedules/<int:pk>/', schedule_detail, name='instructorschedule-detail'),
    path('api/v1/instructor-schedules/<int:pk>/reservations/', schedule_reservations, name='instructorschedule-reservations'),

    # Ticket endpoints
    path('api/v1/tickets/', ticket_list, name='ticket-list'),
    path('api/v1/tickets/<int:pk>/', ticket_detail, name='ticket-detail'),

    # SessionReservation endpoints
    path('api/v1/session-reservations/', reservation_list, name='sessionreservation-list'),
    path('api/v1/session-reservations/<int:pk>/', reservation_detail, name='sessionreservation-detail'),

    # Apply / Cancel
    path('api/v1/apply-session/<int:schedule_id>/', ApplySessionView.as_view(), name='apply-session'),
    path('api/v1/cancel-session/<int:schedule_id>/', CancelSessionView.as_view(), name='cancel-session'),
    
    # Practice Session endpoints
    path('api/v1/practice-sessions/', practice_list, name='practicesession-list'),
    path('api/v1/practice-sessions/<int:pk>/', practice_detail, name='practicesession-detail'),
    path('api/v1/practice-sessions/<int:pk>/waiting-position/', practice_waiting, name='practicesession-waiting'),
    
    # Practice Reservation endpoints
    path('api/v1/practice-reservations/', practice_reservation_list, name='practicereservation-list'),
    path('api/v1/practice-reservations/<int:pk>/', practice_reservation_detail, name='practicereservation-detail'),
    
    # My reservations
    path('api/v1/my-reservations/', MyReservationsView.as_view(), name='my-reservations'),
] 