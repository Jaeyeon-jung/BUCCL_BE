from django.db import models
from django.conf import settings
from buccl_back.choices import *
from buccl_user.models import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, F

# 1. 기본 모델 (Base models)
class Sport(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "스포츠 종류"
        verbose_name_plural = "스포츠 종류 관리"

    def __str__(self):
        return self.name

class Location(models.Model):
     name = models.CharField(max_length=100, unique=True, db_index=True)
     address = models.CharField(max_length=255, blank=True, null=True)
     image = models.ImageField(upload_to='locations/', blank=True, null=True)
     operating_hours = models.CharField(max_length=255, blank=True, null=True)
     category = models.CharField(max_length=50, blank=True, null=True, db_index=True)
     pricing = models.CharField(max_length=255, blank=True, null=True)
     facilities = models.JSONField(default=list, blank=True, null=True)
     latitude = models.FloatField(blank=True, null=True)
     longitude = models.FloatField(blank=True, null=True)
     sports = models.ManyToManyField('Sport', related_name='locations', blank=True)     

     class Meta:
        verbose_name = "장소"
        verbose_name_plural = "장소 관리"
        ordering = ['name']

     def __str__(self):
         return self.name

class ProductType(models.Model):
    """상품 유형 정의 모델"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=20, unique=True) 
    requires_schedule = models.BooleanField(default=False)
    has_sessions = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "상품 유형"
        verbose_name_plural = "상품 유형 관리"
    
    def __str__(self):
        return self.name

# 2. 상품 관련 모델 (Product related models)
class TravelProduct(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=200)
    guide = models.CharField(max_length=100)
    requirements = models.TextField()
    max_participants = models.IntegerField()
    detailed_content = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="비용")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_travel_products', null=True)

    class Meta:
        verbose_name = "여행 상품"
        verbose_name_plural = "여행 상품 관리"

    def __str__(self):
        return self.name

class ClassProduct(models.Model):
    title = models.CharField(max_length=255)
    brand = models.CharField(max_length=100)
    main_image = models.ImageField(upload_to='class_products/', null=True, blank=True)
    
    # 가격 관련 필드
    original_price = models.DecimalField(max_digits=10, decimal_places=0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    discount_rate = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "클래스 상품"
        verbose_name_plural = "클래스 상품 관리"

    def save(self, *args, **kwargs):
        # discount_price가 있을 때만 할인율 자동 계산
        if self.discount_price and self.original_price and self.original_price > 0:
            # 할인율 = (원가 - 할인가) / 원가 * 100
            self.discount_rate = int(((self.original_price - self.discount_price) / self.original_price) * 100)
        else:
            self.discount_rate = 0
        
        super().save(*args, **kwargs)
    
    @property
    def display_price(self):
        """표시할 가격 결정: discount_price 있으면 그것, 없으면 original_price"""
        return self.discount_price if self.discount_price else self.original_price

    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(ClassProduct, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='class_products/images/')
    is_detail = models.BooleanField(default=False)

    class Meta:
        verbose_name = "상품 이미지"
        verbose_name_plural = "상품 이미지 관리"

    def __str__(self):
        type_label = "상세 이미지" if self.is_detail else "추가 이미지"
        return f"{self.product.title} - {type_label}"

class Product(models.Model):
    """모든 상품 정보 관리 모델"""
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=0)
    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    # 상품 유형별 외래키 - 이 상품의 구체적인 정보가 담긴 모델을 연결
    class_product = models.ForeignKey(ClassProduct, on_delete=models.SET_NULL, null=True, blank=True, related_name='generic_products')
    travel_product = models.ForeignKey(TravelProduct, on_delete=models.SET_NULL, null=True, blank=True, related_name='generic_products')
    lesson_product = models.ForeignKey('buccl_lessons.LessonProduct', on_delete=models.SET_NULL, null=True, blank=True, related_name='generic_products')
    
    # 상품 메타데이터 - JSONField는 신중히 사용. 자주 검색되거나 구조화된 데이터는 별도 필드/모델 고려
    attributes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "통합 상품"
        verbose_name_plural = "통합 상품 관리"
        ordering = ['name']

    def clean(self):
        super().clean()
        # product_type에 따라 해당 specific product만 설정되었는지 확인
        type_code = self.product_type.code.upper()
        specific_products_populated = sum([
            1 if self.class_product else 0,
            1 if self.travel_product else 0,
            1 if self.lesson_product else 0,
        ])

        if specific_products_populated == 0 and self.pk: # pk check for new unsaved instances
             # This validation might be too strict if a generic product can exist without a specific type initially
             # Consider if a product must always have a specific linked product if product_type is set
             pass


        if specific_products_populated > 1:
            raise ValidationError("하나의 상품 유형(클래스, 여행, 레슨)만 연결할 수 있습니다.")

        if type_code == 'CLASS' and not self.class_product:
            raise ValidationError("상품 유형이 '클래스'인 경우 클래스 상품 정보(class_product)를 연결해야 합니다.")
        elif type_code == 'TRAVEL' and not self.travel_product:
            raise ValidationError("상품 유형이 '여행'인 경우 여행 상품 정보(travel_product)를 연결해야 합니다.")
        elif type_code == 'LESSON' and not self.lesson_product: # Assuming 'LESSON' is a code in ProductType
            raise ValidationError("상품 유형이 '레슨'인 경우 레슨 상품 정보(lesson_product)를 연결해야 합니다.")

        # Ensure other specific product fields are null
        if type_code != 'CLASS' and self.class_product:
            self.class_product = None
        if type_code != 'TRAVEL' and self.travel_product:
            self.travel_product = None
        if type_code != 'LESSON' and self.lesson_product: # Assuming 'LESSON' is a code in ProductType
            self.lesson_product = None


    def save(self, *args, **kwargs):
        self.full_clean() # Validate before saving
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.product_type.name})"

# 3. 주문 및 결제 모델 (Order and payment)
class Order(models.Model):
    """주문/구매 정보 관리 모델"""
    ORDER_STATUS_CHOICES = (
        ('PENDING', '결제 대기'),         # 주문 생성, 아직 결제 시작 전
        ('PAYMENT_ATTEMPTED', '결제 시도 중'), # 사용자가 결제 정보 입력 및 인증 요청 시도
        ('PAYMENT_PROCESSING', '결제 처리 중'),# 인증 성공 후 승인 요청 진행 중
        ('CONFIRMED', '확정됨'),          # 결제 최종 성공
        ('CANCELLED', '취소됨'),        # 주문/결제 취소
        ('COMPLETED', '완료됨'),        # (상품 유형에 따라) 배송/사용 완료 등
        ('PAYMENT_FAILED', '결제 실패'),    # 인증 또는 승인 실패
    )
    
    PRODUCT_TYPE_CHOICES = (
        ('LESSON', '레슨'),
        ('CLASS', '클래스'),
        ('TRAVEL', '여행'),
        ('PRODUCT', '일반 상품'), # This implies a generic product without specific FKs in Product model
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    # 실제 결제 상품 (정적 상품, 클래스 상품 등) - Product 모델을 통해 모든 상품 유형을 참조
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)

    # 프런트/백엔드 로직에서 자주 쓰는 문자열 코드 - product.product_type.code 로 대체 가능하나, 편의를 위해 유지 가능
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)

    # 개별 유형에 대한 참조 (nullable) - Product 모델로 이전됨
    # class_product = models.ForeignKey('ClassProduct', on_delete=models.SET_NULL, null=True, blank=True)
    # travel_product = models.ForeignKey('TravelProduct', on_delete=models.SET_NULL, null=True, blank=True)
    # lesson_product = models.ForeignKey('buccl_lessons.LessonProduct', on_delete=models.SET_NULL, null=True, blank=True)

    quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=0) # 금액 필드 DecimalField로 변경
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING', db_index=True)
    # order_details: Consider normalizing if it contains structured data for querying.
    order_details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 결제 흐름 추적을 위한 추가 필드 (선택적)
    last_payment_attempt_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "주문"
        verbose_name_plural = "주문 관리"
        ordering = ['-created_at']
    
    def __str__(self):
        product_name = "무상품"
        if self.product:
            product_name = self.product.name
        # elif self.lesson_product: # Removed
        #     product_name = self.lesson_product.title
        return f"{self.user.user_id} - {product_name} - {self.status}"

class Payment(models.Model):
    """결제 정보만 관리하는 모델"""
    PAYMENT_FLOW_STATUS_CHOICES = (
        ('AUTH_REQUESTED', '인증 요청됨'),
        ('AUTH_SUCCESS', '인증 성공'),
        ('AUTH_FAILED', '인증 실패'),
        ('CAPTURE_REQUESTED', '승인 요청됨'),
        ('CAPTURE_SUCCESS', '승인 성공 (결제 완료)'),
        ('CAPTURE_FAILED', '승인 실패'),
        ('CANCEL_REQUESTED', '취소 요청됨'),
        ('CANCEL_SUCCESS', '취소 성공'),
        ('CANCEL_FAILED', '취소 실패'),
        ('REFUNDED', '환불됨'), # 부분/전체 환불의 최종 상태
        ('SYSTEM_ERROR', '시스템 오류'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', db_index=True)
    attempt_number = models.PositiveIntegerField(default=1, db_index=True, help_text='동일 주문 내 결제 시도 횟수 (1부터 자동)')
    amount = models.DecimalField(max_digits=10, decimal_places=0) # 최종 결제/승인 금액
    # status 필드를 좀 더 세분화된 결제 흐름 상태로 변경
    status = models.CharField(max_length=20, choices=PAYMENT_FLOW_STATUS_CHOICES, db_index=True)
    payment_method_type = models.CharField(max_length=20, null=True, blank=True) # 예: CARD, BANK_TRANSFER 등 PG사 제공 코드
    payment_method_detail = models.CharField(max_length=100, null=True, blank=True) # 예: 신한카드, KB국민은행 등
    
    pg_provider = models.CharField(max_length=50, default='nicepay') # PG사 정보 (확장성)
    moid = models.CharField(max_length=100, db_index=True, unique=True)  # 상점 주문번호 (PG사 전달용, Payment Detail과 중복될 수 있으나 편의상 추가)
    tid = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # PG사 거래번호 (인증/승인 후 발급)
    
    # 시간 정보
    created_at = models.DateTimeField(auto_now_add=True, db_index=True) # Payment 레코드 생성 시간
    updated_at = models.DateTimeField(auto_now=True)
    # paid_at, cancelled_at 등은 PaymentDetail 또는 별도 이벤트 로그로 관리하거나, status 변화에 따라 업데이트
    auth_requested_at = models.DateTimeField(null=True, blank=True) # 인증 요청 시간
    auth_completed_at = models.DateTimeField(null=True, blank=True) # 인증 응답 수신 시간 (성공/실패 무관)
    capture_requested_at = models.DateTimeField(null=True, blank=True) # 승인 요청 시간
    capture_completed_at = models.DateTimeField(null=True, blank=True) # 승인 응답 수신 시간 (최종 결제 완료 시간으로 간주 가능)
    last_failed_at = models.DateTimeField(null=True, blank=True) # 마지막 실패 시간
    
    error_code = models.CharField(max_length=50, null=True, blank=True) # 마지막 오류 코드
    error_message = models.TextField(null=True, blank=True) # 마지막 오류 메시지

    # === JSON으로 대체 가능한 부분 ===
    # 결제 수단 상세 (카드사, 은행코드 등)
    payment_method_details = models.JSONField(default=dict, blank=True)
    
    # 시간 추적 (타임스탬프 모음)
    event_timestamps = models.JSONField(default=dict, blank=True)
    # 예: {'auth_requested_at': '2023-06-01T12:34:56', 'auth_completed_at': '2023-06-01T12:35:00'}
    
    # 오류 정보
    error_data = models.JSONField(default=dict, blank=True)
    # 예: {'code': 'ERR123', 'message': '카드 한도 초과', 'details': {...}}

    class Meta:
        verbose_name = "결제 주요 정보"
        verbose_name_plural = "결제 주요 정보 관리"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # attempt_number 자동 부여 (새 레코드일 때만)
        if not self.pk and self.order_id and (self.attempt_number == 1 or self.attempt_number is None):
            # 현재까지 시도된 결제 수를 계산하여 +1
            current_attempts = Payment.objects.filter(order_id=self.order_id).count()
            self.attempt_number = current_attempts + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order.user.user_id} - attempt#{self.attempt_number} - {self.moid} - {self.amount}원 - {self.get_status_display()}"
            
    # save 메소드에서 상태 변경에 따른 시간 자동 설정 등은 비즈니스 로직 복잡도에 따라 서비스 계층에서 처리하는 것을 고려

    def get_buyer_name(self):
        """요청 데이터에서 구매자 이름을 가져옵니다"""
        # auth_request 관계를 통해 구매자 정보 접근
        if hasattr(self, 'auth_request') and hasattr(self.auth_request, 'buyer_info'):
            return self.auth_request.buyer_info.get('name')
        
        # capture_response에서 구매자 정보 확인
        if hasattr(self, 'capture_response') and self.capture_response.buyer_name:
            return self.capture_response.buyer_name
            
        return None

    @staticmethod
    def save_payment_data(order, data_dict):
        """결제 데이터를 저장하는 정적 메서드"""
        # DB 컬럼 + JSON 필드에 모두 저장하여 데이터 누락 방지
        payment = Payment.objects.create(
            order=order,
            moid=data_dict.get('Moid'),
            amount=data_dict.get('Amt') or 0,
            status='AUTH_REQUESTED',
            payment_method_type=data_dict.get('PayMethod'),
            # JSON 필드에는 원본 그대로 저장
            payment_method_details={'raw': data_dict}
        )
        return payment

class PaymentAuthRequest(models.Model):
    """결제 인증 요청 파라미터 저장 모델"""
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='auth_request')
    
    # 핵심 필드 (직접 쿼리 대상) - 컬럼 유지
    goods_name = models.CharField(max_length=100, null=True)
    amt = models.DecimalField(max_digits=10, decimal_places=0)
    mid = models.CharField(max_length=50)
    moid = models.CharField(max_length=100)
    sign_data = models.TextField(null=True)
    pay_method = models.CharField(max_length=20)
    
    # === JSON으로 대체 가능한 부분 ===
    # 1. 구매자 정보 그룹
    buyer_info = models.JSONField(default=dict)
    # {'name': '홍길동', 'tel': '01012345678', 'email': 'user@example.com'}
    
    # 2. 금액 상세 그룹
    amount_details = models.JSONField(default=dict)
    # {'supply_amt': 9091, 'goods_vat': 909, 'service_amt': 0, 'tax_free_amt': 0}
    
    # 3. UI/설정 옵션 그룹
    ui_options = models.JSONField(default=dict)
    # {'np_lang': 'KR', 'skin_type': 'BLUE', 'conn_with_iframe': 'N', ...}
    
    # 4. 카드/결제 설정 그룹
    payment_config = models.JSONField(default=dict)
    # {'card_number_masked': '123456*1234', 'card_expiry': '2412', ...}
    
    # 5. 전체 원본 데이터 (백업)
    raw_data = models.JSONField(default=dict)

    class Meta:
        verbose_name = "PG 인증 요청 정보"
        verbose_name_plural = "PG 인증 요청 정보 관리"
    
    def __str__(self):
        return f"인증요청: {self.payment.order.moid if hasattr(self.payment, 'order') and hasattr(self.payment.order, 'moid') else self.payment_id}"


class PaymentAuthResponse(models.Model):
    """결제 인증 응답 파라미터 저장 모델"""
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='auth_response')
    
    # === 인증 응답 파라미터 (NicePay Response) ===
    result_code = models.CharField(max_length=10, null=True, blank=True)  # AuthResultCode
    result_msg = models.TextField(null=True, blank=True)  # AuthResultMsg
    auth_token = models.CharField(max_length=100, null=True, blank=True)  # AuthToken
    pay_method = models.CharField(max_length=20, null=True, blank=True)  # PayMethod
    mid = models.CharField(max_length=50, null=True, blank=True)  # MID
    moid = models.CharField(max_length=100, null=True, blank=True)  # Moid
    amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # Amt
    signature = models.TextField(null=True, blank=True)  # Signature
    req_reserved = models.TextField(null=True, blank=True)  # ReqReserved
    tx_tid = models.CharField(max_length=100, null=True, blank=True)  # TxTid
    next_app_url = models.URLField(max_length=400, null=True, blank=True)  # NextAppURL
    net_cancel_url = models.URLField(max_length=400, null=True, blank=True)  # NetCancelURL
    
    # 추가 인증 정보
    auth_date = models.DateTimeField(null=True, blank=True)  # 인증 시각
    card_code = models.CharField(max_length=10, null=True, blank=True)  # 카드사 코드
    card_name = models.CharField(max_length=50, null=True, blank=True)  # 카드사명
    card_type = models.CharField(max_length=10, null=True, blank=True)  # 카드 종류 (신용/체크 등)
    pg_tid = models.CharField(max_length=100, null=True, blank=True)  # 인증 성공 시 PG TID
    
    # 전체 전문
    raw_data = models.JSONField(default=dict, blank=True)  # 인증 응답 전체
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "PG 인증 응답 정보"
        verbose_name_plural = "PG 인증 응답 정보 관리"
    
    def __str__(self):
        return f"인증응답: {self.payment.order.moid if hasattr(self.payment, 'order') and hasattr(self.payment.order, 'moid') else self.payment_id} - {self.result_code}"


class PaymentCaptureRequest(models.Model):
    """결제 승인 요청 파라미터 저장 모델"""
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='capture_request')
    
    # === 승인 요청 파라미터 ===
    tid = models.CharField(max_length=100, null=True, blank=True)  # TID
    auth_token = models.CharField(max_length=100, null=True, blank=True)  # AuthToken
    mid = models.CharField(max_length=50, null=True, blank=True)  # MID
    amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # Amt
    edi_date = models.CharField(max_length=20, null=True, blank=True)  # EdiDate
    sign_data = models.TextField(null=True, blank=True)  # SignData
    char_set = models.CharField(max_length=20, null=True, blank=True)  # CharSet
    edi_type = models.CharField(max_length=20, null=True, blank=True)  # EdiType
    mall_reserved = models.TextField(null=True, blank=True)  # MallReserved
    
    # 전체 전문
    raw_data = models.JSONField(default=dict, blank=True)  # 승인 요청 전체 파라미터
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "PG 승인 요청 정보"
        verbose_name_plural = "PG 승인 요청 정보 관리"
    
    def __str__(self):
        return f"승인요청: {self.payment.order.moid if hasattr(self.payment, 'order') and hasattr(self.payment.order, 'moid') else self.payment_id}"


class PaymentCaptureResponse(models.Model):
    """결제 승인 응답 파라미터 저장 모델"""
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='capture_response')
    
    # === 승인 응답 파라미터 ===
    result_code = models.CharField(max_length=10, null=True, blank=True)  # ResultCode
    result_msg = models.TextField(null=True, blank=True)  # ResultMsg
    amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # Amt
    mid = models.CharField(max_length=50, null=True, blank=True)  # MID
    moid = models.CharField(max_length=100, null=True, blank=True)  # Moid
    signature = models.TextField(null=True, blank=True)  # Signature
    buyer_email = models.CharField(max_length=100, null=True, blank=True)  # BuyerEmail
    buyer_tel = models.CharField(max_length=20, null=True, blank=True)  # BuyerTel
    buyer_name = models.CharField(max_length=50, null=True, blank=True)  # BuyerName
    goods_name = models.CharField(max_length=100, null=True, blank=True)  # GoodsName
    tid = models.CharField(max_length=100, null=True, blank=True)  # TID
    auth_code = models.CharField(max_length=50, null=True, blank=True)  # AuthCode
    auth_date = models.CharField(max_length=20, null=True, blank=True)  # AuthDate (문자열)
    auth_datetime = models.DateTimeField(null=True, blank=True)  # AuthDate (날짜 객체로 변환)
    pay_method = models.CharField(max_length=20, null=True, blank=True)  # PayMethod
    cart_data = models.TextField(null=True, blank=True)  # CartData
    mall_reserved = models.TextField(null=True, blank=True)  # MallReserved
    
    # 계좌이체/가상계좌 추가 응답 필드
    bank_code = models.CharField(max_length=20, null=True, blank=True)  # BankCode or VbankBankCode
    bank_name = models.CharField(max_length=50, null=True, blank=True)  # BankName or VbankBankName
    rcpt_type = models.CharField(max_length=20, null=True, blank=True)  # RcptType
    rcpt_tid = models.CharField(max_length=100, null=True, blank=True)  # RcptTID
    rcpt_auth_code = models.CharField(max_length=50, null=True, blank=True)  # RcptAuthCode
    vbank_num = models.CharField(max_length=30, null=True, blank=True)  # VbankNum
    vbank_exp_date = models.CharField(max_length=10, null=True, blank=True)  # VbankExpDate
    vbank_exp_time = models.CharField(max_length=10, null=True, blank=True)  # VbankExpTime
    
    # 추가 필드
    card_acquirer_code = models.CharField(max_length=10, null=True, blank=True)  # 매입 카드사 코드
    card_acquirer_name = models.CharField(max_length=50, null=True, blank=True)  # 매입 카드사명
    
    # 전체 전문
    raw_data = models.JSONField(default=dict, blank=True)  # 승인 응답 전체
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "PG 승인 응답 정보"
        verbose_name_plural = "PG 승인 응답 정보 관리"
    
    def __str__(self):
        return f"승인응답: {self.payment.order.moid if hasattr(self.payment, 'order') and hasattr(self.payment.order, 'moid') else self.payment_id} - {self.result_code}"

class PaymentCancel(models.Model):
    """결제 취소 정보 관리 모델"""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='cancellations', db_index=True)
    cancel_amount = models.DecimalField(max_digits=10, decimal_places=0)
    requested_at = models.DateTimeField(auto_now_add=True)  # 취소 요청 시각
    completed_at = models.DateTimeField(null=True, blank=True)  # 취소 완료 시각 (PG 응답 기준)
    
    reason = models.TextField(verbose_name="취소 사유")
    is_partial_cancel = models.BooleanField(default=False)  # 부분취소 여부
    remain_amount = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # 잔액
    
    pg_cancel_tid = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # PG사 취소 거래번호
    status = models.CharField(max_length=20, choices=Payment.PAYMENT_FLOW_STATUS_CHOICES, null=True, blank=True, db_index=True)  # 취소 요청 상태
    
    # 추가 JSON 필드
    cancel_details = models.JSONField(default=dict, blank=True)  # 취소 관련 추가 정보
    
    class Meta:
        verbose_name = "결제 취소 정보"
        verbose_name_plural = "결제 취소 정보 관리"
        ordering = ['-requested_at']
    
    def __str__(self):
        cancel_type = "부분취소" if self.is_partial_cancel else "전체취소"
        return f"{cancel_type}: {self.payment.moid} - {self.cancel_amount}원 - {self.get_status_display() if self.status else 'N/A'}"

class PaymentCancelRequest(models.Model):
    """결제 취소 요청 파라미터 저장 모델"""
    payment_cancel = models.OneToOneField(PaymentCancel, on_delete=models.CASCADE, related_name='cancel_request')
    
    # === 취소 요청 파라미터 ===
    tid = models.CharField(max_length=100, null=True, blank=True)  # TID
    mid = models.CharField(max_length=50, null=True, blank=True)  # MID
    moid = models.CharField(max_length=100, null=True, blank=True)  # Moid
    cancel_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # CancelAmt
    cancel_msg = models.TextField(null=True, blank=True)  # CancelMsg
    partial_cancel_code = models.CharField(max_length=20, null=True, blank=True)  # PartialCancelCode
    edi_date = models.CharField(max_length=20, null=True, blank=True)  # EdiDate
    sign_data = models.TextField(null=True, blank=True)  # SignData
    
    # 금액 상세
    supply_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # SupplyAmt
    goods_vat = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # GoodsVat
    service_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # ServiceAmt
    tax_free_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # TaxFreeAmt
    
    # 기타 설정
    char_set = models.CharField(max_length=20, null=True, blank=True)  # CharSet
    cart_type = models.CharField(max_length=20, null=True, blank=True)  # CartType
    edi_type = models.CharField(max_length=20, null=True, blank=True)  # EdiType
    mall_reserved = models.TextField(null=True, blank=True)  # MallReserved
    
    # 환불 계좌 정보 (가상계좌 취소시)
    refund_acct_no = models.CharField(max_length=50, null=True, blank=True)  # RefundAcctNo
    refund_bank_cd = models.CharField(max_length=20, null=True, blank=True)  # RefundBankCd
    refund_acct_nm = models.CharField(max_length=50, null=True, blank=True)  # RefundAcctNm
    
    # 전체 전문
    raw_data = models.JSONField(default=dict, blank=True)  # 취소 요청 전체 파라미터
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "PG 취소 요청 정보"
        verbose_name_plural = "PG 취소 요청 정보 관리"
    
    def __str__(self):
        payment_id = self.payment_cancel.payment_id if hasattr(self.payment_cancel, 'payment_id') else 'N/A'
        return f"취소요청: {payment_id} - {self.cancel_amt or 0}원"


class PaymentCancelResponse(models.Model):
    """결제 취소 응답 파라미터 저장 모델"""
    payment_cancel = models.OneToOneField(PaymentCancel, on_delete=models.CASCADE, related_name='cancel_response')
    
    # === 취소 응답 파라미터 ===
    result_code = models.CharField(max_length=10, null=True, blank=True)  # ResultCode
    result_msg = models.TextField(null=True, blank=True)  # ResultMsg
    error_cd = models.CharField(max_length=10, null=True, blank=True)  # ErrorCD
    error_msg = models.TextField(null=True, blank=True)  # ErrorMsg
    cancel_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # CancelAmt
    mid = models.CharField(max_length=50, null=True, blank=True)  # MID
    moid = models.CharField(max_length=100, null=True, blank=True)  # Moid
    signature = models.TextField(null=True, blank=True)  # Signature
    pay_method = models.CharField(max_length=20, null=True, blank=True)  # PayMethod
    tid = models.CharField(max_length=100, null=True, blank=True)  # TID
    otid = models.CharField(max_length=100, null=True, blank=True)  # OTID (원거래 TID)
    cancel_date = models.CharField(max_length=10, null=True, blank=True)  # CancelDate
    cancel_time = models.CharField(max_length=10, null=True, blank=True)  # CancelTime
    cancel_num = models.CharField(max_length=50, null=True, blank=True)  # CancelNum
    remain_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # RemainAmt
    mall_reserved = models.TextField(null=True, blank=True)  # MallReserved
    
    # 신용카드 취소 추가 응답 필드
    coupon_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # CouponAmt
    clickpay_cl = models.CharField(max_length=20, null=True, blank=True)  # ClickpayCl
    multi_card_acqu_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # MultiCardAcquAmt
    multi_point_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # MultiPointAmt
    multi_coupon_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # MultiCouponAmt
    multi_rcpt_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # MultiRcptAmt
    
    # 전체 전문
    raw_data = models.JSONField(default=dict, blank=True)  # 취소 응답 전체
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "PG 취소 응답 정보"
        verbose_name_plural = "PG 취소 응답 정보 관리"
    
    def __str__(self):
        payment_id = self.payment_cancel.payment_id if hasattr(self.payment_cancel, 'payment_id') else 'N/A'
        return f"취소응답: {payment_id} - {self.result_code}"


class PaymentNetCancelRequest(models.Model):
    """망 취소 요청 파라미터 저장 모델"""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='net_cancel_requests')
    
    # === 망 취소 요청 파라미터 ===
    tid = models.CharField(max_length=100, null=True, blank=True)  # TID
    auth_token = models.CharField(max_length=100, null=True, blank=True)  # AuthToken
    mid = models.CharField(max_length=50, null=True, blank=True)  # MID
    amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # Amt
    edi_date = models.CharField(max_length=20, null=True, blank=True)  # EdiDate
    net_cancel = models.CharField(max_length=5, null=True, blank=True)  # NetCancel (Y)
    sign_data = models.TextField(null=True, blank=True)  # SignData
    char_set = models.CharField(max_length=20, null=True, blank=True)  # CharSet
    edi_type = models.CharField(max_length=20, null=True, blank=True)  # EdiType
    mall_reserved = models.TextField(null=True, blank=True)  # MallReserved
    
    # 전체 전문
    raw_data = models.JSONField(default=dict, blank=True)  # 망 취소 요청 전체 파라미터
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "PG 망 취소 요청 정보"
        verbose_name_plural = "PG 망 취소 요청 정보 관리"
    
    def __str__(self):
        return f"망취소요청: {self.payment.order.moid if hasattr(self.payment, 'order') and hasattr(self.payment.order, 'moid') else self.payment_id}"


class PaymentNetCancelResponse(models.Model):
    """망 취소 응답 파라미터 저장 모델"""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='net_cancel_responses')
    net_cancel_request = models.OneToOneField(PaymentNetCancelRequest, on_delete=models.CASCADE, related_name='response', null=True, blank=True)
    
    # === 망 취소 응답 파라미터 ===
    result_code = models.CharField(max_length=10, null=True, blank=True)  # ResultCode
    result_msg = models.TextField(null=True, blank=True)  # ResultMsg
    error_cd = models.CharField(max_length=10, null=True, blank=True)  # ErrorCD
    error_msg = models.TextField(null=True, blank=True)  # ErrorMsg
    cancel_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # CancelAmt
    mid = models.CharField(max_length=50, null=True, blank=True)  # MID
    moid = models.CharField(max_length=100, null=True, blank=True)  # Moid
    signature = models.TextField(null=True, blank=True)  # Signature
    pay_method = models.CharField(max_length=20, null=True, blank=True)  # PayMethod
    tid = models.CharField(max_length=100, null=True, blank=True)  # TID
    cancel_date = models.CharField(max_length=10, null=True, blank=True)  # CancelDate
    cancel_time = models.CharField(max_length=10, null=True, blank=True)  # CancelTime
    cancel_num = models.CharField(max_length=50, null=True, blank=True)  # CancelNum
    remain_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # RemainAmt
    mall_reserved = models.TextField(null=True, blank=True)  # MallReserved
    
    # 신용카드 망 취소 추가 응답 필드
    coupon_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # CouponAmt
    clickpay_cl = models.CharField(max_length=20, null=True, blank=True)  # ClickpayCl
    multi_card_acqu_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # MultiCardAcquAmt
    multi_point_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # MultiPointAmt
    multi_coupon_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # MultiCouponAmt
    multi_rcpt_amt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)  # MultiRcptAmt
    
    # 전체 전문
    raw_data = models.JSONField(default=dict, blank=True)  # 망 취소 응답 전체
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "PG 망 취소 응답 정보"
        verbose_name_plural = "PG 망 취소 응답 정보 관리"
    
    def __str__(self):
        return f"망취소응답: {self.payment.order.moid if hasattr(self.payment, 'order') and hasattr(self.payment.order, 'moid') else self.payment_id} - {self.result_code}"

# 6. 리뷰 관련 모델 (Reviews)
class ClassReview(models.Model):
    # product 필드는 ClassProduct 대신 Product 모델을 참조하도록 변경 고려 (만약 리뷰가 모든 Product 유형에 해당된다면)
    # 현재는 ClassProduct에 대한 리뷰로 유지
    product = models.ForeignKey(ClassProduct, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    rating = models.PositiveIntegerField(choices=[(1,1), (2,2), (3,3), (4,4), (5,5)])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "클래스 리뷰"
        verbose_name_plural = "클래스 리뷰 관리"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.user_id} - {self.product.title} - {self.rating}점"

class ReviewImage(models.Model):
    review = models.ForeignKey(ClassReview, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "리뷰 이미지"
        verbose_name_plural = "리뷰 이미지 관리"

    def __str__(self):
        return f"Review {self.review.id} Image"