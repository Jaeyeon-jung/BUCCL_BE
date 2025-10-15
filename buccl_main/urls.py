from django.urls import path
from .views import (
    ImageUploadView, 
    PaymentResult, 
    PaymentRetryAli, 
    PrePaymentCheckView,
    SaveTravelProductView,
    TravelProductListView,
    TravelProductDetailView,
    GetTravelProductView,
    UpdateTravelProductView,
    DeleteTravelProductView,
    PrePaymentCheckTravelView,
    ReviewListView,
    UserReviewsView,
    ReviewCreateView,
    ReviewDetailView,
)
from django.conf import settings
from django.conf.urls.static import static

app_name = "buccl_main"

urlpatterns = [
    # 결제 관련 URLs
    path("api/v1/payment-result/", PaymentResult.as_view(), name="payment_result"),
    path("api/v1/payment-retry-ali/", PaymentRetryAli.as_view(), name="payment_retry_ali"),
    path("api/v1/payment-validation/", PrePaymentCheckView.as_view(), name="payment_validation"),
    
    # 이미지 업로드
    path("api/v1/upload-image/", ImageUploadView.as_view(), name="upload_image"),
    
    # 리뷰 관련 URL 패턴
    path("api/v1/products/<int:product_id>/reviews/", ReviewListView.as_view(), name="product-reviews"),
    path("api/v1/reviews/my/", UserReviewsView.as_view(), name="user-reviews"),
    path("api/v1/products/<int:product_id>/reviews/create/", ReviewCreateView.as_view(), name="create-review"),
    path("api/v1/reviews/<int:review_id>/", ReviewDetailView.as_view(), name="review-detail"),
    
    # 여행 상품 관련 URLs
    path("api/v1/save-travel-product/", SaveTravelProductView.as_view(), name="save_travel_product"),
    path("api/v1/travel-products/", TravelProductListView.as_view(), name="travel_product_list"),
    path("api/v1/travel-products/<int:pk>/", TravelProductDetailView.as_view(), name="travel_product_detail"),
    path("api/v1/get-travel-product/<int:product_id>/", GetTravelProductView.as_view(), name="get_travel_product"),
    path("api/v1/delete-product/<int:product_id>/", DeleteTravelProductView.as_view(), name="delete_travel_product"),
    path("api/v1/pre-payment-check-travel/", PrePaymentCheckTravelView.as_view(), name="pre_payment_check_travel"),
    path("api/v1/update-travel-product/<int:product_id>/", UpdateTravelProductView.as_view(), name="update_travel_product"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
