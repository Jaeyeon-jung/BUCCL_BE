import logging
from .models import User, CertificateUpload, UserLevel
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

logger = logging.getLogger("django")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "user_id",
            "password",
            "level",
            "name",
            "user_email",
            "hp",
            "is_staff",
            "is_admin",
        ]

    def create(self, validated_data):
        user = User.objects.create_user(
            user_id=validated_data["user_id"],
            password=validated_data["password"],
            name=validated_data.get("name", ""),
            user_email=validated_data.get("user_email", ""),
            hp=validated_data.get("hp", ""),
            is_staff=validated_data.get("is_staff", 0),
        )
        return user


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "user_id",
            "password",
            "name",
            "user_email",
            "user_gender",
            "user_birthday",
            "level",
            "hp",
            "auth",
            "terms_accepted",
            "age_confirmed",
            "privacy_accepted",
            "is_staff",
        ]

    def save(self, **kwargs):
        logger.debug(
            "RegisterSerializer save method called with data: %s", self.validated_data
        )
        level = self.validated_data.get("level", "0")  # 기본값을 '0'으로 설정
        level = int(level)
        is_staff = (
            1 if self.validated_data.get("is_staff", 0) else 0
        )  # 기본값을 '0'으로 설정
        logger.debug("user info: %s", self.validated_data)
        user = User.objects.create_user(
            user_id=self.validated_data["user_id"],
            password=self.validated_data["password"],
            name=self.validated_data["name"],
            user_email=self.validated_data["user_email"],
            user_gender=self.validated_data["user_gender"],
            user_birthday=self.validated_data["user_birthday"],
            level=level,
            hp=self.validated_data["hp"],
            auth=self.validated_data["auth"],
            terms_accepted=self.validated_data["terms_accepted"],
            age_confirmed=self.validated_data["age_confirmed"],
            privacy_accepted=self.validated_data["privacy_accepted"],
            is_staff=is_staff,
        )

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = user.user_id  # 문자열 user_id
        return token


"""
        if user.user_type == "2":
            NormalUser.objects.create(
                user = user
            )
        elif user.user_type == "3":
            Pharmacist.objects.create(
                user = user
            )
        elif user.user_type == "4":
            ParmStaff.objects.create(
                user = user
            )
"""


class CertificateUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateUpload
        fields = [
            "id",
            "user",
            "certificate_name",
            "certificate_file",
            "uploaded_at",
            "is_approved",
        ]
        read_only_fields = ["id", "uploaded_at", "is_approved"]

    def create(self, validated_data):
        # 최초 업로드 시 승인 상태는 기본적으로 False
        validated_data["is_approved"] = False
        return super().create(validated_data)


class UserLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLevel
        fields = ["id", "level", "name", "description", "sport_id"]
