from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
    OpenApiParameter,
    OpenApiResponse,
)
from .serializers import *


class UserSchema:
    user_auth_info = extend_schema(
        methods=["GET"],  # 이 데코레이터를 적용할 HTTP 메서드
        summary="유저 정보",  # API 요약 설명
        description="유저 정보 API입니다.",  # API 상세 설명
    )

    user_login = extend_schema(
        methods=["POST"],  # 이 데코레이터를 적용할 HTTP 메서드
        summary="로그인",  # API 요약 설명
        description="로그인 API입니다.",  # API 상세 설명
        request=inline_serializer(
            name="LoginSerializer",
            fields={
                "user_id": serializers.CharField(max_length=45),  # 유저 아이디
                "password": serializers.CharField(max_length=255),  # 비밀번호
            },
        ),  # 요청 스키마
    )

    user_info = extend_schema(
        methods=["GET"],
        summary="User 정보",
        description="User 정보 API.",
    )

    """
    user register input example:

    request_input = {
    "user_id": "test",
    "password": "1234",
    "name": "donguk",
    "user_email": "xxx@xxx.com",
    "hp": "01012345678",
    "auth": 1,
    "user_gender": "M",
    "user_birthday": "2025-04-16",
    "level": "1",
    "terms_accepted": 1,
    "age_confirmed": 1,
    "privacy_accepted": 1,
    }
    """
    user_register = extend_schema(
        methods=["POST"],
        summary="User 회원가입",
        description="User 회원가입 API.",
        request=inline_serializer(
            name="LoginSerializer",
            fields={
                "user_id": serializers.CharField(),  # 유저 아이디
                "password": serializers.CharField(),  # 비밀번호
                "name": serializers.CharField(),  # 이름
                "user_email": serializers.CharField(),  # 이메일
                "hp": serializers.CharField(),  # 휴대번호
                "auth": serializers.IntegerField(),  # 인증
                "user_gender": serializers.CharField(),  # 성별
                "user_birthday": serializers.CharField(),  # 생일
                "level": serializers.CharField(),  # 회원, 강사여부
                "terms_accepted": serializers.IntegerField(),  # 약관동의여부
                "age_confirmed": serializers.IntegerField(),  # 14세이상 여부
                "privacy_accepted": serializers.IntegerField(),  # 개인정보수집 및 이용동의 여부
            },
        ),  # 요청 스키마
    )

    certificate_upload = extend_schema(
        methods=["POST"],
        summary="자격증 업로드",
        description="자격증 업로드 API.",
        request=inline_serializer(
            name="CertificateUploadSerializer",
            fields={
                "certificate_type": serializers.CharField(),
                "certificate_number": serializers.CharField(),
                "issue_date": serializers.DateField(),
                "expiry_date": serializers.DateField(),
                "certificate_file": serializers.FileField(),
            },
        ),
    )

    user_levels = extend_schema(
        methods=["GET"],
        summary="User 레벨 목록",
        description="User 레벨 목록 API.",
    )
