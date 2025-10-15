from django.db import models
from django.conf import settings
from django.utils import timezone
from buccl_main.models import Sport
from django.db.models import F, Q # F, Q 임포트

class LessonProduct(models.Model):
    """판매용 강습권 (n회 이용권)"""
    sport = models.ForeignKey('buccl_main.Sport', on_delete=models.PROTECT, related_name='lesson_specific_products', db_index=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    sessions_count = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '레슨 상품 (강습권)'
        verbose_name_plural = '레슨 상품 (강습권) 관리'
        ordering = ['title']

    def __str__(self):
        return self.title

class InstructorSchedule(models.Model):
    """강사가 생성하는 일정(TimeTable)"""

    lesson_product = models.ForeignKey(
        LessonProduct,
        on_delete=models.CASCADE,
        related_name='schedules',
        db_index=True
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='instructor_schedules',
        db_index=True
    )

    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.ForeignKey('buccl_main.Location', on_delete=models.PROTECT, db_index=True)

    capacity = models.PositiveIntegerField()
    current_bookings = models.PositiveIntegerField(default=0)

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN', db_index=True)

    version = models.PositiveIntegerField(default=0) # 낙관적 잠금을 위한 버전 필드

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '강사 스케줄'
        verbose_name_plural = '강사 스케줄 관리'
        ordering = ['date', 'start_time']
        constraints = [
            models.UniqueConstraint(fields=['instructor', 'date', 'start_time', 'location'], name='unique_instructor_schedule_slot'),
            models.CheckConstraint(check=Q(end_time__gt=F('start_time')), name='check_start_end_time')
        ]

    def __str__(self):
        return f"{self.lesson_product.title} | {self.date} {self.start_time}-{self.end_time} ({self.instructor.user_id})"

    @property
    def available_spots(self):
        return self.capacity - self.current_bookings

    def increment_bookings(self):
        """Increments bookings atomically. Call this from views/services."""
        InstructorSchedule.objects.filter(pk=self.pk).update(current_bookings=F('current_bookings') + 1)
        self.refresh_from_db()

    def decrement_bookings(self):
        """Decrements bookings atomically. Call this from views/services."""
        InstructorSchedule.objects.filter(pk=self.pk).update(current_bookings=F('current_bookings') - 1)
        self.refresh_from_db()

class Ticket(models.Model):
    """LessonProduct 구매 후 발급되는 티켓"""

    # 주문과 1:1 관계 (결제 완료 후 활성화)
    order = models.OneToOneField('buccl_main.Order', on_delete=models.CASCADE, related_name='lesson_ticket', null=True, blank=True, db_index=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets',
        db_index=True
    )
    lesson_product = models.ForeignKey(
        LessonProduct,
        on_delete=models.PROTECT,
        related_name='tickets',
        db_index=True
    )

    sessions_total = models.PositiveIntegerField()
    sessions_used = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=False, db_index=True)

    STATUS_CHOICES = [
        ('UNUSED', 'Unused'),
        ('PARTIALLY_USED', 'Partially Used'),
        ('FULLY_USED', 'Fully Used'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNUSED', db_index=True)

    valid_until = models.DateField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '레슨 티켓'
        verbose_name_plural = '레슨 티켓 관리'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.user_id} | {self.lesson_product.title} ({self.sessions_used}/{self.sessions_total}) - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Status 계산
        if not self.pk and self.lesson_product:
            self.sessions_total = self.lesson_product.sessions_count

        if self.status == 'CANCELLED':
            pass
        elif self.valid_until and timezone.now().date() > self.valid_until and self.status != 'FULLY_USED':
            self.status = 'EXPIRED'
        elif self.sessions_used == 0:
            self.status = 'UNUSED'
        elif self.sessions_used >= self.sessions_total:
            self.status = 'FULLY_USED'
            self.is_active = False
        else:
            self.status = 'PARTIALLY_USED'

        if self.order and self.order.status not in ['PENDING', 'CANCELLED'] and not self.is_active and self.status not in ['EXPIRED', 'FULLY_USED', 'CANCELLED']:
            self.is_active = True
        elif self.order and self.order.status == 'CANCELLED':
            self.is_active = False
            self.status = 'CANCELLED'

        super().save(*args, **kwargs)

class SessionReservation(models.Model):
    """티켓 1회 사용과 스케줄을 연결"""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='reservations',
        db_index=True
    )
    schedule = models.ForeignKey(
        InstructorSchedule,
        on_delete=models.CASCADE,
        related_name='reservations',
        db_index=True
    )

    # For sequential reservations
    day_order = models.PositiveIntegerField(null=True, blank=True)
    is_theory = models.BooleanField(default=False)
    
    # For waitlist functionality
    is_waiting = models.BooleanField(default=False, db_index=True)
    queue_position = models.PositiveIntegerField(null=True, blank=True)

    STATUS_CHOICES = [
        ('RESERVED', 'Reserved'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('NOSHOW', 'No-Show'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='RESERVED', db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = '레슨 세션 예약'
        verbose_name_plural = '레슨 세션 예약 관리'
        unique_together = ('ticket', 'schedule')
        ordering = ['schedule', 'queue_position', 'created_at']

    def __str__(self):
        wait_status = " (대기)" if self.is_waiting else ""
        return f"티켓 {self.ticket_id} | 스케줄 {self.schedule_id}{wait_status} - {self.get_status_display()}"

# ---------------------- Practice (Free Session) ----------------------
class PracticeSession(models.Model):
    """연습 세션 (자율 연습반) - 기존 buccl_practice 모델을 통합"""

    base_schedule = models.OneToOneField(
        'InstructorSchedule',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='based_practice_session',
    )

    title = models.CharField(max_length=100, blank=True)
    sport = models.ForeignKey('buccl_main.Sport', on_delete=models.PROTECT, db_index=True)
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='practice_sessions', db_index=True)

    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.ForeignKey('buccl_main.Location', on_delete=models.PROTECT, db_index=True)

    capacity = models.PositiveIntegerField()
    current_bookings = models.PositiveIntegerField(default=0)

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN', db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '자율 연습 세션'
        verbose_name_plural = '자율 연습 세션 관리'
        ordering = ['date', 'start_time']

    def __str__(self):
        display_title = self.title or self.sport.name
        return f"{display_title} | {self.date} {self.start_time}-{self.end_time} ({self.get_status_display()})"

    @property
    def available_spots(self):
        return self.capacity - self.current_bookings

    # helper for waiting list
    def waiting_reservations(self):
        return self.reservations.filter(is_waiting=True).order_by('queue_position')

    def waiting_count(self):
        return self.waiting_reservations().count()

    def increment_bookings(self):
        PracticeSession.objects.filter(pk=self.pk).update(current_bookings=F('current_bookings') + 1)
        self.refresh_from_db()

    def decrement_bookings(self):
        PracticeSession.objects.filter(pk=self.pk).update(current_bookings=F('current_bookings') - 1)
        self.refresh_from_db()

class PracticeReservation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='practice_reservations', db_index=True)
    practice_session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, related_name='reservations', db_index=True)

    STATUS_CHOICES = [
        ('RESERVED', 'Reserved'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('NOSHOW', 'No-Show'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='RESERVED', db_index=True)

    is_waiting = models.BooleanField(default=False, db_index=True)
    queue_position = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = '자율 연습 예약'
        verbose_name_plural = '자율 연습 예약 관리'
        unique_together = ('user', 'practice_session')
        ordering = ['practice_session', 'is_waiting', 'queue_position', 'created_at']

    def __str__(self):
        state = '대기' if self.is_waiting else '예약'
        return f"{self.user.user_id} | {self.practice_session_id} ({state}) - {self.get_status_display()}" 