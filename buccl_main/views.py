from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import ClassProduct, ClassReview, TravelProduct
from .serializers import ClassReviewSerializer, TravelProductSerializer
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
import os


class ImageUploadView(APIView):
    """이미지 업로드 API"""
    def post(self, request):
        if 'image' not in request.FILES:
            return Response(
                {"error": "No image file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image = request.FILES['image']
        
        # 파일 확장자 추출
        ext = image.name.split('.')[-1]
        # 고유한 파일명 생성
        filename = f"{uuid.uuid4()}.{ext}"
        
        # 파일 저장
        path = default_storage.save(f"uploads/{filename}", ContentFile(image.read()))
        
        # 전체 URL 생성
        url = request.build_absolute_uri(default_storage.url(path))
        
        return Response({"url": url}, status=status.HTTP_201_CREATED)


class PaymentResult(APIView):
    """결제 결과 처리 API"""
    def post(self, request):
        # TODO: 실제 결제 처리 로직 구현
        return Response({"message": "Payment result received"}, status=status.HTTP_200_OK)


class PaymentRetryAli(APIView):
    """결제 재시도 API"""
    def post(self, request):
        # TODO: 실제 결제 재시도 로직 구현
        return Response({"message": "Payment retry initiated"}, status=status.HTTP_200_OK)


class PrePaymentCheckView(APIView):
    """결제 전 검증 API"""
    def post(self, request):
        # TODO: 실제 결제 전 검증 로직 구현
        return Response({"valid": True}, status=status.HTTP_200_OK)


# Travel Product Views (view_groups가 없으므로 여기에 직접 구현)
class SaveTravelProductView(APIView):
    """여행 상품 저장"""
    def post(self, request):
        serializer = TravelProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TravelProductListView(APIView):
    """여행 상품 목록"""
    def get(self, request):
        products = TravelProduct.objects.all()
        serializer = TravelProductSerializer(products, many=True)
        return Response(serializer.data)


class TravelProductDetailView(APIView):
    """여행 상품 상세"""
    def get(self, request, pk):
        product = get_object_or_404(TravelProduct, pk=pk)
        serializer = TravelProductSerializer(product)
        return Response(serializer.data)


class GetTravelProductView(APIView):
    """여행 상품 조회"""
    def get(self, request, product_id):
        product = get_object_or_404(TravelProduct, pk=product_id)
        serializer = TravelProductSerializer(product)
        return Response(serializer.data)


class UpdateTravelProductView(APIView):
    """여행 상품 수정"""
    def put(self, request, product_id):
        product = get_object_or_404(TravelProduct, pk=product_id)
        serializer = TravelProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteTravelProductView(APIView):
    """여행 상품 삭제"""
    def delete(self, request, product_id):
        product = get_object_or_404(TravelProduct, pk=product_id)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PrePaymentCheckTravelView(APIView):
    """여행 상품 결제 전 검증"""
    def post(self, request):
        # TODO: 실제 여행 상품 결제 전 검증 로직 구현
        return Response({"valid": True}, status=status.HTTP_200_OK)


# Review Views
class ReviewListView(APIView):
    """상품별 리뷰 목록"""
    def get(self, request, product_id):
        product = get_object_or_404(ClassProduct, pk=product_id)
        reviews = product.reviews.all()
        serializer = ClassReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class UserReviewsView(APIView):
    """사용자의 리뷰 목록"""
    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        reviews = ClassReview.objects.filter(user=request.user)
        serializer = ClassReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ReviewCreateView(APIView):
    """리뷰 작성"""
    def post(self, request, product_id):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        product = get_object_or_404(ClassProduct, pk=product_id)
        data = request.data.copy()
        data['product'] = product.id
        data['user'] = request.user.id
        
        serializer = ClassReviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user, product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewDetailView(APIView):
    """리뷰 상세 조회"""
    def get(self, request, review_id):
        review = get_object_or_404(ClassReview, pk=review_id)
        serializer = ClassReviewSerializer(review)
        return Response(serializer.data) 