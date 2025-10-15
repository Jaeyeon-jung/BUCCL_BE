from django.contrib import admin
from buccl_user.models import User
from .models import (
    # 기존 모델 유지
    Sport, Location, 
    ClassProduct, ProductImage, ClassReview, ReviewImage,
    TravelProduct,
    Product, ProductType, Order, Payment
)
from django import forms
from django.utils.html import format_html
from django.db.models import Count

# 기본 등록 모델들은 유지
@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('name', 'course_count')
    search_fields = ('name',)
    
    def course_count(self, obj):
        # SportsCourse 모델이 없으므로 0 반환
        return 0
    
    course_count.short_description = '코스 수'

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'category')
    search_fields = ('name', 'address', 'category')
    list_filter = ('category',)
    filter_horizontal = ('sports',)
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'address', 'category')
        }),
        ('시설 정보', {
            'fields': ('operating_hours', 'pricing', 'facilities')
        }),
        ('위치 정보', {
            'fields': ('latitude', 'longitude', 'image')
        }),
        ('제공 스포츠', {
            'fields': ('sports',)
        }),
    )

# 새로운 모델 등록
@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'requires_schedule', 'has_sessions')
    search_fields = ('name', 'code')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_type', 'base_price', 'is_active', 'created_at')
    list_filter = ('product_type', 'is_active')
    search_fields = ('name', 'description')
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'description', 'product_type', 'base_price', 'is_active')
        }),
        ('상품 연결', {
            'fields': ('class_product', 'travel_product', 'lesson_product')
        }),
        ('추가 정보', {
            'fields': ('attributes', 'created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__user_id', 'user__name', 'product__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('주문 정보', {
            'fields': ('user', 'product', 'quantity', 'total_amount', 'status')
        }),
        ('추가 정보', {
            'fields': ('order_details', 'created_at', 'updated_at')
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'status', 'payment_method_type', 'created_at', 'capture_completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__user__user_id', 'order__user__name', 'tid')
    readonly_fields = ('created_at', 'updated_at', 'auth_completed_at', 'capture_completed_at')
    fieldsets = (
        ('결제 정보', {
            'fields': ('order', 'amount', 'status', 'payment_method_type', 'payment_method_detail', 'tid')
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at', 'auth_completed_at', 'capture_completed_at')
        }),
        ('추가 정보', {
            'fields': ('payment_method_details', 'error_data')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__user', 'order__product')


# 나머지 모델 어드민 유지
@admin.register(TravelProduct)
class TravelProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'date_range', 'guide', 'max_participants', 'price', 'created_at')
    list_filter = ('location', 'start_date', 'end_date', 'guide')
    search_fields = ('name', 'location', 'guide', 'requirements', 'detailed_content')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'location', 'start_date', 'end_date', 'guide', 'max_participants', 'price')
        }),
        ('상세 정보', {
            'fields': ('requirements', 'detailed_content')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at', 'creator')
        }),
    )
    
    def date_range(self, obj):
        return f"{obj.start_date} ~ {obj.end_date}"
    
    date_range.short_description = '기간'

# 클래스 상품 관련 부분은 유지하되 일부 수정
# ProductImageInline, ClassReviewInline 유지
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_detail', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "이미지 없음"
    
    image_preview.short_description = '이미지 미리보기'

class ClassReviewInline(admin.TabularInline):
    model = ClassReview
    extra = 0
    fields = ('user', 'rating', 'content', 'created_at')
    readonly_fields = ('user', 'rating', 'content', 'created_at')
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(ClassProduct)
class ClassProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'brand', 'price_display', 'discount_rate', 'review_count', 'created_at')
    list_filter = ('brand', 'created_at', 'discount_rate')
    search_fields = ('title', 'brand')
    readonly_fields = ('created_at', 'updated_at', 'review_count', 'main_image_preview', 'discount_rate')
    inlines = [ProductImageInline, ClassReviewInline]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'brand', 'main_image', 'main_image_preview')
        }),
        ('가격 정보', {
            'fields': ('original_price', 'discount_price', 'discount_rate')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at', 'review_count')
        }),
    )
    
    def price_display(self, obj):
        if obj.discount_price:
            return f'{obj.discount_price:,}원 (원가: {obj.original_price:,}원)'
        return f'{obj.original_price:,}원'
    
    def review_count(self, obj):
        return obj.reviews.count()
    
    def main_image_preview(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="200" />', obj.main_image.url)
        return "이미지 없음"
    
    price_display.short_description = '판매가'
    review_count.short_description = '리뷰 수'
    main_image_preview.short_description = '메인 이미지 미리보기'

# ReviewImageInline 및 ClassReview, ProductImage 어드민 유지
class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 1
    fields = ('image', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "이미지 없음"
    
    image_preview.short_description = '이미지 미리보기'

@admin.register(ClassReview)
class ClassReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating_stars', 'content_preview', 'image_count', 'created_at')
    list_filter = ('rating', 'created_at', 'product')
    search_fields = ('user__user_id', 'user__name', 'product__title', 'content')
    readonly_fields = ('created_at', 'updated_at', 'rating_stars')
    inlines = [ReviewImageInline]
    
    fieldsets = (
        ('리뷰 정보', {
            'fields': ('user', 'product', 'rating', 'rating_stars')
        }),
        ('리뷰 내용', {
            'fields': ('content',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def rating_stars(self, obj):
        rating = obj.rating or 0  # None이면 0으로 처리
        return '★' * rating + '☆' * (5 - rating)
    
    def content_preview(self, obj):
        if len(obj.content) > 100:
            return f"{obj.content[:100]}..."
        return obj.content
    
    def image_count(self, obj):
        return obj.images.count()
    
    rating_stars.short_description = '평점'
    content_preview.short_description = '리뷰 내용'
    image_count.short_description = '이미지 수'

# ClassOrder 관련 어드민 제거하고 ProductImage 어드민은 유지
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_detail', 'image_preview')
    list_filter = ('is_detail', 'product')
    search_fields = ('product__title',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "이미지 없음"
    
    image_preview.short_description = '이미지 미리보기'