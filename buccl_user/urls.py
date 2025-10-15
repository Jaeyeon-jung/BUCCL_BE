from . import views

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

app_name = "buccl_user"

urlpatterns = [
    path("test_view/", views.test_view),
    path("register/", views.RegisterAPIView.as_view()),  # post - 회원가입
    path(
        "auth/", views.AuthAPIView.as_view()
    ),  # post - 로그인, delete - 로그아웃, get - 유저정보
    path("auth/refresh/", TokenRefreshView.as_view()),  # jwt 토큰 재발급
    path(
        "api/v1/id-validation/", views.IdValidation.as_view(), name="id_validataion"
    ),  # id validation
    path(
        "api/v1/hp-validation/", views.HPValidation.as_view(), name="hp_validation"
    ),  # hp validation
    path(
        "api/v1/auth-message/", views.AuthView.as_view(), name="auth_message"
    ),  # hp 인증번호 전송 및 저장
    path(
        "api/v1/auth-check/", views.Check_auth.as_view(), name="auth_check"
    ),  # hp 인증번호 check
    path(
        "api/v1/user-info/<str:user_id>/",
        views.UserInfoView.as_view(),
        name="user_info",
    ),
    path(
        "api/v1/certificates/upload/",
        views.CertificateUploadView.as_view(),
        name="certificate-upload",
    ),  # 자격증 최초 업로드 (유저가 자격증 제출)
    path(
        "api/v1/certificates/<int:certificate_id>/approve/",
        views.CertificateApproveView.as_view(),
        name="certificate-approve",
    ),  # 자격증 승인/반려 (관리자 전용)
    path(
        "api/v1/certificates/<int:certificate_id>/reupload/",
        views.CertificateReUploadView.as_view(),
        name="certificate-reupload",
    ),  # 자격증 재등록 (유저가 반려된 자격증 다시 업로드)
    path("api/v1/user_levels/", views.UserLevelsView.as_view(), name="user_level"),  # 유저 레벨 목록
]
