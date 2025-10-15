from .models import (
    Sport, Location,
    Product, ProductType, Order, Payment, PaymentCancel,
    TravelProduct, ClassProduct, 
    ProductImage, ClassReview, ReviewImage
)
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()

class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'

class PaymentCancelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentCancel
        fields = [
            'id', 'payment', 'cancel_amount', 'requested_at', 
            'reason', 'is_partial_cancel', 'remain_amount',
            'pg_cancel_tid', 'status', 'cancel_details'
        ]

class TravelProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelProduct
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_detail']

class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image']

class ClassReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_id = serializers.CharField(source='user.user_id', read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ClassReview
        fields = [
            'id', 'user_id', 'user_name', 'rating', 'content', 
            'images', 'created_at'
        ]

class ClassProductListSerializer(serializers.ModelSerializer):
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassProduct
        fields = [
            'id', 'brand', 'title', 'discount_price',
            'discount_rate', 'original_price', 'main_image', 'review_count'
        ]
        
    def get_review_count(self, obj):
        return obj.reviews.count()

class ClassProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ClassReviewSerializer(many=True, read_only=True)
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = ClassProduct
        fields = [
            'id', 'brand', 'title', 'original_price',
            'discount_price', 'discount_rate', 'main_image', 
            'images', 'reviews', 'review_count', 'average_rating',
            'created_at', 'updated_at'
        ]
        
    def get_review_count(self, obj):
        return obj.reviews.count()
        
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return 0
        total_rating = sum(review.rating for review in reviews)
        return round(total_rating / len(reviews), 1)

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = '__all__'

class ClassProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassProduct
        fields = '__all__'