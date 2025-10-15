from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.utils import timezone

from .models import (
    LessonProduct, InstructorSchedule, Ticket, 
    SessionReservation, PracticeSession, PracticeReservation
)

# LessonProduct Admin
@admin.register(LessonProduct)
class LessonProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'sport', 'sessions_count', 'price', 'created_at')
    list_filter = ('sport', 'created_at')
    search_fields = ('title', 'description', 'sport__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'sport', 'description')
        }),
        ('세션 및 가격', {
            'fields': ('sessions_count', 'price')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# SessionReservation Inline
class SessionReservationInline(admin.TabularInline):
    model = SessionReservation
    extra = 0
    fields = ('ticket', 'status', 'day_order', 'is_theory', 'is_waiting', 'queue_position')
    readonly_fields = ('created_at', 'cancelled_at')

# InstructorSchedule Admin
@admin.register(InstructorSchedule)
class InstructorScheduleAdmin(admin.ModelAdmin):
    list_display = ('lesson_product', 'instructor', 'date', 'time_display', 'location', 'capacity', 'current_bookings', 'status')
    list_filter = ('status', 'date', 'lesson_product', 'instructor')
    search_fields = ('lesson_product__title', 'instructor__user_id', 'instructor__name', 'location__name')
    readonly_fields = ('created_at', 'updated_at', 'current_bookings')
    inlines = [SessionReservationInline]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('lesson_product', 'instructor')
        }),
        ('일정 정보', {
            'fields': ('date', 'start_time', 'end_time', 'location')
        }),
        ('예약 정보', {
            'fields': ('capacity', 'current_bookings', 'status')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def time_display(self, obj):
        return f"{obj.start_time} - {obj.end_time}"
    
    time_display.short_description = '시간'

# Ticket Admin
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson_product', 'sessions_total', 'sessions_used', 'status', 'valid_until')
    list_filter = ('status', 'created_at')
    search_fields = ('user__user_id', 'user__name', 'lesson_product__title')
    readonly_fields = ('sessions_used', 'created_at', 'updated_at')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'lesson_product', 'order')
        }),
        ('세션 정보', {
            'fields': ('sessions_total', 'sessions_used', 'status', 'valid_until')
        }),
        ('활성화 정보', {
            'fields': ('is_active',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# SessionReservation Admin
@admin.register(SessionReservation)
class SessionReservationAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'schedule', 'status', 'day_order', 'is_theory', 'is_waiting', 'created_at')
    list_filter = ('status', 'is_theory', 'is_waiting', 'created_at')
    search_fields = ('ticket__user__user_id', 'ticket__user__name', 'schedule__lesson_product__title')
    readonly_fields = ('created_at', 'cancelled_at')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('ticket', 'schedule')
        }),
        ('예약 상세', {
            'fields': ('status', 'day_order', 'is_theory')
        }),
        ('대기 정보', {
            'fields': ('is_waiting', 'queue_position')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'cancelled_at')
        }),
    )
    
    actions = ['cancel_reservations']
    
    @admin.action(description='선택한 예약 취소')
    def cancel_reservations(self, request, queryset):
        updated = queryset.update(status='CANCELLED', cancelled_at=timezone.now())
        self.message_user(request, f'{updated}개의 예약이 취소되었습니다.')

# PracticeReservation Inline
class PracticeReservationInline(admin.TabularInline):
    model = PracticeReservation
    extra = 0
    fields = ('user', 'status', 'is_waiting', 'queue_position')
    readonly_fields = ('created_at',)

# PracticeSession Admin
@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'sport', 'instructor', 'date', 'time_display', 'location', 'capacity', 'current_bookings', 'status')
    list_filter = ('status', 'date', 'sport', 'instructor', 'location')
    search_fields = ('title', 'sport__name', 'instructor__user_id', 'instructor__name')
    readonly_fields = ('created_at', 'updated_at', 'current_bookings', 'waiting_count_display')
    inlines = [PracticeReservationInline]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'sport', 'instructor', 'base_schedule')
        }),
        ('일정 정보', {
            'fields': ('date', 'start_time', 'end_time', 'location')
        }),
        ('예약 정보', {
            'fields': ('capacity', 'current_bookings', 'waiting_count_display', 'status')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def time_display(self, obj):
        return f"{obj.start_time} - {obj.end_time}"
    
    def waiting_count_display(self, obj):
        return obj.waiting_count()
    
    time_display.short_description = '시간'
    waiting_count_display.short_description = '대기자 수'

# PracticeReservation Admin
@admin.register(PracticeReservation)
class PracticeReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'practice_session', 'status', 'waiting_status', 'created_at')
    list_filter = ('status', 'is_waiting', 'created_at')
    search_fields = ('user__user_id', 'user__name', 'practice_session__title', 'practice_session__sport__name')
    readonly_fields = ('created_at', 'cancelled_at')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'practice_session')
        }),
        ('예약 상세', {
            'fields': ('status', 'is_waiting', 'queue_position')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'cancelled_at')
        }),
    )
    
    def waiting_status(self, obj):
        if obj.is_waiting:
            return f'대기 ({obj.queue_position}번)'
        return '예약'
    
    waiting_status.short_description = '예약 상태'
    
    actions = ['cancel_reservations']
    
    @admin.action(description='선택한 예약 취소')
    def cancel_reservations(self, request, queryset):
        updated = queryset.update(status='CANCELLED', cancelled_at=timezone.now())
        self.message_user(request, f'{updated}개의 예약이 취소되었습니다.') 