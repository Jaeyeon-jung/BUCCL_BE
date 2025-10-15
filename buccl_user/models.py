import os, hmac, json, time, base64, random, datetime, hashlib, requests, uuid, logging
from buccl_back.choices import *
from buccl_main.models import Sport
from model_utils.models import TimeStampedModel

from django.utils import timezone
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model

logger = logging.getLogger('django')

class UserManager(BaseUserManager):
    def create_user(self, user_id, password, hp, auth, **extra_fields):
        if not user_id:
            raise ValueError('사용자 ID는 필수입니다.')
        user = self.model(
            user_id = user_id,
            hp = hp,
            auth = auth,                         
            **extra_fields
        )
        user.set_password(password)        
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, hp, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        # extra_fields.setdefault('level', 0)  # default 레벨을 0으로 설정

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # auth 매개변수를 None으로 설정
        return self.create_user(user_id, password, hp, auth=None, **extra_fields)

# class UserLevel(models.Model):
#     level = models.IntegerField(unique=True)
#     name = models.CharField(max_length=50)
#     description = models.TextField(blank=True)

#     def __str__(self):
#         return f"{self.level} - {self.name}"

class UserLevel(models.Model):
    level = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    sport = models.ForeignKey(
        'buccl_main.Sport', 
        on_delete=models.SET_NULL,  # Sport가 삭제되면 NULL로 설정
        null=True,  # NULL 값 허용
        blank=True,  # 폼에서 필수 입력 필드가 아님
        related_name='user_levels',  # Sport에서 역참조용
        db_index=True # 스포츠별 레벨 조회 성능 향상
    )

    def __str__(self):
        sport_name = self.sport.name if self.sport else "일반"
        return f"{sport_name} - {self.level} - {self.name}"

class User(AbstractBaseUser, PermissionsMixin):
    '''
    회원 정보 테이블, 테이블명 USER_TB
    user_id : 유저 아이디
    password : 비밀번호
    hp : 휴대폰번호
    user_email : 사용자 이메일
    level : user 등급, default 0, 프리다이빙 일반 11, 프리다이빙 초급 12, 프리다이빙 중급 13, 프리다이빙 고급 14...
    auth : 인증번호 6자리
    date_joined : 가입일, auto_now_add 사용

    agree_UserInfo : 개인정보이용동의
    agree_Marketing : 마케팅 이용동의

    
    is_active : 사용자 활성화 여부
    is_admin : 관리자 여부
    is_staff : 강사 여부
    is_superuser : superuser 여부
    '''
    objects = UserManager()
    
    user_id = models.CharField(max_length=40, verbose_name="아이디", unique=True, db_index=True)
    password = models.CharField(max_length=255, verbose_name="비밀번호")
    name = models.CharField(max_length=30, verbose_name="이름", db_index=True)
    hp = models.CharField(max_length=12, verbose_name="휴대폰번호", null=True, unique=True, db_index=True)
    user_email = models.CharField(max_length=50, verbose_name="이메일", null=True, unique=True, db_index=True)
    user_gender = models.CharField(choices=GENDER_CHOICES, max_length=10, verbose_name="성별", null=True, blank=True)
    user_birthday = models.DateField(verbose_name="생년월일", null=True, blank=True)
    
    # level 필드를 UserLevel 모델을 참조하는 ForeignKey로 변경
    level = models.ForeignKey(
        UserLevel, 
        on_delete=models.SET_NULL, # 등급이 삭제되어도 사용자는 유지 (null 허용)
        null=True, 
        blank=True, 
        verbose_name="User 등급",
        db_index=True
    )
    auth = models.CharField(max_length=6, verbose_name="인증번호", null=True) # 인증 완료 후 삭제 또는 비활성화 고려
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='가입일', null=True, blank=True, db_index=True)
    terms_accepted = models.BooleanField(verbose_name="이용약관동의", default=False)
    age_confirmed = models.BooleanField(verbose_name="연령확인", default=False)
    privacy_accepted = models.BooleanField(verbose_name="개인정보수집동의", default=False)

    is_active = models.BooleanField(default=True, db_index=True)
    is_admin = models.BooleanField(default=False) # is_staff 또는 별도 권한 그룹 사용 고려
    is_staff = models.BooleanField(default=False, db_index=True) # Django admin 접근 권한 및 강사 구분
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['hp']       

    def __str__(self):
        return self.user_id
        
    def get_short_name(self):
        # 짧은 이름을 반환합니다. Admin 페이지에서 사용됩니다.
        return self.name or self.user_id
    
    def get_full_name(self):
        # 전체 이름을 반환합니다. Admin 페이지에서 사용됩니다.
        return self.name or self.user_id

    class Meta:
        db_table = "buccl_user"
        verbose_name = "사용자"
        verbose_name_plural = "사용자 계정 관리"
        ordering = ['-date_joined', 'user_id']
    
    def check_admin_privileges(self):
        return self.is_admin or self.is_superuser or self.is_staff

class AuthSMS(TimeStampedModel):
    '''
    회원가입 문자 인증을 위한 model, 테이블명 AUTH_TB
    네이버 sens 서비스를 통해 입력한 휴대폰 번호로 인증 번호를 보냅니다.
    인증 코드는 6자리 숫자입니다.
    '''
    hp = models.CharField(max_length=11, verbose_name='휴대폰번호', primary_key=True)
    auth = models.IntegerField(verbose_name='인증번호')

    class Meta:
        db_table = 'AUTH_TB'

    def save(self, *args, **kwargs):
        self.auth = random.randint(100000, 1000000) # 난수로 6자리 문자 인증 번호 생성
        super().save(*args, **kwargs)
        self.send_sms() # 문자 전송용 함수

    def send_sms(self):
        # 중요: 이 부분은 동기적으로 외부 API를 호출합니다.
        # 운영 환경에서는 Celery와 같은 비동기 작업 큐를 사용하여 SMS 발송을 처리하는 것이 좋습니다.
        # 이렇게 하면 API 응답 지연이나 오류가 사용자 요청 처리에 직접적인 영향을 미치는 것을 방지할 수 있습니다.
        ##### 네이버 sens 서비스 이용 위한 json request 형식 #####
        timestamp = str(int(time.time() * 1000))

        url = "https://sens.apigw.ntruss.com"
        uri = "/sms/v2/services/ncp:sms:kr:328805329142:nuseum/messages"
        apiUrl = url + uri

        access_key = settings.NAVER_SENS_ACCESS_KEY
        secret_key = bytes(settings.NAVER_SENS_SECRET_KEY, 'UTF-8')
        message = bytes("POST" + " " + uri + "\n" + timestamp + "\n" + access_key, 'UTF-8')
        
        try:
            signingKey = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest())

            body = {
                "type" : "SMS",
                "contentType" : "COMM",
                "from" : "01091161927",
                "subject" : "subject",
                "content" : "[버킷리스트 클래스] 인증 번호 [{}]를 입력해주세요.".format(self.auth),
                "messages" : [{"to" : self.hp}]
            }
            body2 = json.dumps(body)
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "x-ncp-apigw-timestamp": timestamp,
                "x-ncp-iam-access-key": access_key,
                "x-ncp-apigw-signature-v2": signingKey
            }

            response = requests.post(apiUrl, headers=headers, data=body2)
            logger.debug(f"send_sms response: {response.text}")
        except Exception as e:
            raise Exception(f"SMS 전송 실패: {e}")

    @classmethod
    def check_auth_number(cls, p_num, c_num):
        result = cls.objects.filter(
            hp = p_num,
            auth = c_num,
        )
        logger.debug(f"check_auth_number result: {result}")
        if result:
            return True
        return False    
        

    @classmethod
    def check_timer(cls, p_num, c_num)->bool:
        '''
        문자인증 제한시간을 위한 타이머 설정 함수
        '''
        time_limit = timezone.now() - datetime.timedelta(minutes=5) # minutes 변수를 통해 문자인증 제한시간 설정
        result = cls.objects.filter(
            hp=p_num,
            auth=c_num,
            modified__gte=time_limit
        )

        if result:
            return True
        return False
    
# User = get_user_model()  # 이 라인이 문제를 일으키고 있어 주석 처리했습니다

def unique_file_path(instance, filename):
    # 파일 확장자 분리
    ext = filename.split('.')[-1]
    # UUID로 파일명 생성
    filename = f"{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('certificates', filename)

class CertificateUpload(models.Model):
    user = models.ForeignKey('buccl_user.User', on_delete=models.CASCADE, related_name='certificates', db_index=True)
    certificate_name = models.CharField(max_length=255)
    certificate_file = models.FileField(upload_to=unique_file_path)
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    approved_by = models.ForeignKey(
        'buccl_user.User', 
        null=True, blank=True, 
        related_name='approved_certificates', 
        on_delete=models.SET_NULL,
        db_index=True
    )

    rejected_by = models.ForeignKey(
        'buccl_user.User', 
        null=True, blank=True, 
        related_name='rejected_certificates', 
        on_delete=models.SET_NULL,
        db_index=True
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = '자격증 업로드'
        verbose_name_plural = '자격증 업로드 관리'

    def __str__(self):
        approval_status = '승인' if self.is_approved else ('반려됨' if self.rejection_reason else '대기중') # 상태 세분화
        approver = f" (승인자: {self.approved_by.user_id})" if self.approved_by else ""
        rejector = f" (반려자: {self.rejected_by.user_id})" if self.rejected_by else ""
        return f"{self.user.user_id} - {self.certificate_name} ({approval_status}){approver}{rejector}"
