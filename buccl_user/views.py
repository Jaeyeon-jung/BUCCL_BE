from buccl_user.schemas import UserSchema
import jwt, logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone  # timezone 추가
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction

from buccl_back.settings import SECRET_KEY
from buccl_back.error_code import ErrorCode
from .utils.jwt_auth import get_user_from_token

from .serializers import *
from .models import UserLevel, AuthSMS

logger = logging.getLogger("django")

# Create your views here.
def test_view(request):
    return render(request, 'test.html')

class AuthAPIView(APIView):
    @UserSchema.user_auth_info
    def get(self, request):
        try:
            logger.debug(f"request.COOKIES: {request.COOKIES}")
            # access token을 decode 해서 유저 id 추출 => 유저 식별
            access = request.COOKIES['access']
            payload = jwt.decode(access, SECRET_KEY, algorithms=['HS256'])
            pk = payload.get('user_id')
            user = get_object_or_404(User, pk=pk)
            serializer = UserSerializer(instance=user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except(jwt.exceptions.ExpiredSignatureError):
            # 토큰 만료 시 토큰 갱신
            logger.debug("AuthAPIView ExpiredSignatureError")
            data = {'refresh': request.COOKIES.get('refresh', None)}
            serializer = TokenRefreshSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                access = serializer.data.get('access', None)
                refresh = serializer.data.get('refresh', None)
                payload = jwt.decode(access, SECRET_KEY, algorithms=['HS256'])
                pk = payload.get('user_id')
                user = get_object_or_404(User, pk=pk)
                serializer = UserSerializer(instance=user)
                res = Response(serializer.data, status=status.HTTP_200_OK)
                res.set_cookie('access', access)
                res.set_cookie('refresh', refresh)
                return res
            raise jwt.exceptions.InvalidTokenError

        except(jwt.exceptions.InvalidTokenError):
            # 사용 불가능한 토큰일 때
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @UserSchema.user_login
    def post(self, request):
    	# 유저 인증 self.request, username=user_id, password=password
        logger.debug(f"request.data: {request.data}, self.request: {self.request}")
        user = authenticate(username=request.data.get("user_id"), password=request.data.get("password"))
        # 이미 회원가입 된 유저일 때
        if user is not None:
            serializer = UserSerializer(user)
            # jwt 토큰 접근
            token = CustomTokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)
            
            # 04.17 삭제
            # 사용자가 관리자인지 확인하고 level 설정(superuser일 경우 관리자로 설정)
            # if user.is_superuser or user.is_admin: 
            #     user.is_admin = True
            #     user.save()

            res = Response(
                {
                    "code": "0000",
                    "message": "Login success",
                    "user": serializer.data,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )
            # jwt 토큰 => 쿠키에 저장
            res.set_cookie("access", access_token, httponly=True)
            res.set_cookie("refresh", refresh_token, httponly=True)
            return res
        else:
            return Response(
                {
                    "message": "Login Fail",
                    "code": "1000",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # 로그아웃
    def delete(self, request):
        # 쿠키에 저장된 토큰 삭제 => 로그아웃 처리
        response = Response({
            "code" : "0000",
            "message": "Logout success"
            }, status=status.HTTP_202_ACCEPTED)
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response

class RegisterAPIView(APIView):
    @UserSchema.user_register
    def post(self, request):
        logger.debug(f"RegisterAPIView request.data: {request.data}")
        if User.objects.filter(user_id=request.data['user_id']).exists():   # 중복 아이디 체크
            return Response(
                ErrorCode.ALREADY_REGISTERED,
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():   # 유효성 검증
            user = serializer.save()
            logger.debug(f"RegisterAPIView saved user: {user}")
            
            
        user = authenticate(username=request.data.get("user_id"), password=request.data.get("password"))
        # 유효성 통과 후 저장된 유저일 때
        if user is not None:
            serializer = UserSerializer(user)
            # jwt 토큰 접근
            token = CustomTokenObtainPairSerializer.get_token(user)
            refresh_token = str(token)
            access_token = str(token.access_token)

            # 사용자가 관리자인지 확인하고 level 설정(superuser일 경우 관리자로 설정)
            if user.is_superuser or user.is_admin:
                user.is_admin = True
                user.save()

            res = Response(
                {
                    "code": "0000",
                    "message": "Login success",
                    "user": serializer.data,
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )
            # jwt 토큰 => 쿠키에 저장
            res.set_cookie("access", access_token, httponly=True)
            res.set_cookie("refresh", refresh_token, httponly=True)
            return res
        else:
            return Response(
                {
                    "message": "회원가입 실패",
                    "code": "1001",
                    "detail": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class IdValidation(APIView):
    '''
    중복 아이디가 있는지 검증하는 API
    jquery blur로 AJAX통해 제출.
    '''
    def post(self, request):
        try:
            user_id = request.data['user_id']
            try:
                user = User.objects.get(user_id=user_id)
            except Exception as e:
                user = None
            
            if user is None:
                res =  Response(
                    {
                        "code" : "0001",
                        "message": "id not exist",
                    }                    
                )
            else:
                res =  Response(
                    {
                        "code" : "0002",
                        "message": "id exist",
                    }
                )
            
        except KeyError:
            return Response(
                {
                    "message" : "Bad Request",
                    "code" : "1002",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        else:
            return res

class HPValidation(APIView):
    '''
    중복 휴대폰 번호가 있는지 검증하는 API
    jquery blur로 AJAX통해 제출.
    '''
    def post(self, request):
        try:
            hp = request.data['hp']
            try:
                user = User.objects.get(hp=hp)
            except Exception as e:
                user = None
            
            if user is None:
                res =  Response(
                    {
                        "code" : "0003",
                        "message": "hp not exist",
                    }                    
                )
            else:
                res =  Response(
                    {
                        "code" : "0004",
                        "message": "hp exist",
                    }
                )

        except KeyError:
            return Response(
                {
                    "message" : "Bad Request",
                    "code" : "1003",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        else:
            return res
        
class AuthView(APIView):
    '''
    받은 request data로 휴대폰번호를 통해 AuthSMS에 update_or_create
    인증번호 난수 생성및 저장은 모델 안에 존재.
    '''
    def post(self, request):
        try:
            p_num = request.data['hp']
                  
        except KeyError:
            return Response(
                {
                    "message" : "Bad Request",
                    "code" : "1004",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            AuthSMS.objects.update_or_create(hp=p_num)

            return Response(
                {
                    'message': 'OK', 
                    "code" : "0000",
                    'phone#':request.data['hp']
                }
            )

    #휴대폰번호를 쿼리로 인증번호가 매치되는지 찾는 함수
    #hp, auth 매개변수
    def get(self, request):
        try:    
            p_number = request.data['hp']
            a_number = request.data['auth']
            logging.debug(f"p_number: {p_number}, a_number: {a_number}")    
        except KeyError:
            return Response(
                {
                    "message" : "Bad Request",
                    "code" : "1005",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            result = AuthSMS.objects.check_auth_number(p_number, a_number)
            return Response({"message":"ok", "result":result})
        
class Check_auth(APIView):

    #휴대폰번호를 쿼리로 인증번호가 매치되는지 찾는 함수
    #hp, auth 매개변수

    def post(self, request):
        try:
            user_hp = request.data['hp']
            user_auth = request.data['auth']

            auth = AuthSMS.objects.get(hp=user_hp).auth
            c_auth = str(auth)
            logging.debug(f"c_auth: {c_auth}, user_auth: {user_auth}") 
            if c_auth == user_auth:
                res =  Response(
                            {
                                "code" : "0000",
                                "message": "hp Auth success",
                                "user_auth" : user_auth ,
                                "auth" : auth
                            }                    
                ) 
            elif c_auth != user_auth:
                res =  Response(
                            {
                                "code" : "1005",
                                "message": "hp Auth fail",
                                "user_auth" : user_auth ,
                                "auth" : auth
                            }                    
                        )
        except KeyError:
             return Response(
                {
                    "message" : "Bad Request",
                    "code" : "1005",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            return res

        return res

class UserInfoView(APIView):
    @UserSchema.user_info
    def get(self, request, user_id):
        try:
            # 토큰 검증
            logger.debug(f"request auth: {request.headers.get('Authorization')}")
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return Response({"message": "인증 헤더가 누락되었습니다."}, status=status.HTTP_400_BAD_REQUEST)
            
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # 토큰의 user_id와 요청된 user_id가 일치는지 확인
            if str(payload.get('user_id')) != str(user_id):
                return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
            
            User = get_user_model()
            user = get_object_or_404(User, user_id=user_id)
            
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except jwt.ExpiredSignatureError:
            return Response({"message": "토큰이 만료되었습니다."}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"message": "유효하지 않은 토큰입니다."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CertificateUploadView(APIView):
    @transaction.atomic
    @UserSchema.certificate_upload
    def post(self, request):
        user, error_response = get_user_from_token(request)
        if error_response:
            return error_response

        data = request.data.copy()
        data['user'] = user.id

        serializer = CertificateUploadSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "자격증 업로드 완료", "code": "0000"}, status=status.HTTP_201_CREATED)
        return Response({"message": serializer.errors, "code": "1000"}, status=status.HTTP_400_BAD_REQUEST)
    
# 자격증 승인/거부 (관리자 전용)
class CertificateApproveView(APIView):
    @transaction.atomic
    def post(self, request, certificate_id):
        user, error_response = get_user_from_token(request)
        if error_response:
            return error_response

        # 관리자 권한 체크
        if not user.is_staff:
            return Response({"message": "권한이 없습니다.", "code": "1004"}, status=status.HTTP_403_FORBIDDEN)

        certificate = get_object_or_404(CertificateUpload, id=certificate_id)
        action = request.data.get('action')

        if action == 'approve':
            certificate.is_approved = True
            certificate.rejection_reason = ''
            certificate.approved_by = user
            certificate.rejected_by = None
            certificate.save()
            return Response({"message": "자격증 승인 완료", "code": "0000"}, status=status.HTTP_200_OK)

        elif action == 'reject':
            rejection_reason = request.data.get('rejection_reason', '')
            certificate.is_approved = False
            certificate.rejection_reason = rejection_reason
            certificate.rejected_by = user  # 반려자 정보 기록
            certificate.approved_by = None  # 승인자 정보 삭제 (반려 시 초기화)
            certificate.save()
            return Response({"message": "자격증이 반려되었습니다.", "code": "0001"}, status=status.HTTP_200_OK)

        return Response({"message": "잘못된 요청입니다.", "code": "1005"}, status=status.HTTP_400_BAD_REQUEST)
    
# 자격증 재등록 (반려된 경우 다시 등록)
class CertificateReUploadView(APIView):
    @transaction.atomic
    def post(self, request, certificate_id):
        user, error_response = get_user_from_token(request)
        if error_response:
            return error_response

        certificate = get_object_or_404(CertificateUpload, id=certificate_id, user=user)

        new_file = request.FILES.get('certificate_file')

        if not new_file:
            return Response({"message": "파일이 제공되지 않았습니다.", "code": "1006"}, status=status.HTTP_400_BAD_REQUEST)

        certificate.certificate_file = new_file
        certificate.uploaded_at = timezone.now()
        
        # 승인 및 반려 정보 초기화
        certificate.is_approved = False
        certificate.rejection_reason = ''
        certificate.approved_by = None
        certificate.rejected_by = None

        certificate.save()

        return Response({"message": "자격증 재등록 완료, 승인 대기중입니다.", "code": "0002"}, status=status.HTTP_200_OK)

class UserLevelsView(APIView):
    @UserSchema.user_levels
    def get(self, request):
        user_levels = UserLevel.objects.all()
        serializer = UserLevelSerializer(user_levels, many=True)
        return Response(serializer.data)
