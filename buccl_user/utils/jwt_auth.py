import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

def get_user_from_token(request):
    # 헤더가 아니라 쿠키에서 토큰을 가져오도록 수정
    token = request.COOKIES.get('access')
    if not token:
        return None, Response(
            {"message": "로그인이 필요합니다.", "code": "1001"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        User = get_user_model()
        user = get_object_or_404(User, user_id=user_id)
        return user, None

    except jwt.ExpiredSignatureError:
        return None, Response(
            {"message": "토큰이 만료되었습니다.", "code": "1002"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    except jwt.InvalidTokenError:
        return None, Response(
            {"message": "유효하지 않은 토큰입니다.", "code": "1003"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        return None, Response(
            {"message": str(e), "code": "1007"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
