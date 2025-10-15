from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
    OpenApiParameter,
    OpenApiResponse,
)
from .serializers import *


class MainSchema:
    """
    base_sports: 스포츠 대분류 ex) 프리다이빙, 스쿠버다이빙 ...
    class_product: 스포츠 강습과정 중분류 ex) 프리다이빙 - 입문+초급, 프리다이빙 - 중급 ...
    sport_courses: 스포츠 강습과정 수업 소분류 ex) 프리다이빙 - 입문+초급 - 2025-04-17 19:00~22:00 윤훈빈 강사 ...
    """

    base_sports_courses_list = extend_schema(
        methods=["GET"],  # 이 데코레이터를 적용할 HTTP 메서드
        summary="base_sports_courses list",  # API 요약 설명
        description="base_sports_courses 정보 API. 강습이 기본이 되는 대분류인 스포츠와 해당 스포츠에 해당하는 중분류인 강습과정 정보",
    )

    sport_with_courses = extend_schema(
        methods=["GET"],
        summary="강습 개설된 스포츠 정보 목록",
        description="강습 개설된 스포츠 정보 목록 API. 강습과정이 개설된 스포츠만 조회할 수 있다.",
    )

    sports_courses_all_list = extend_schema(
        methods=["GET"],
        summary="sports_courses_all list",
        description="sports_courses_all 정보 목록 API. 모든 sports course 과정에 정보",
    )

    sports_courses_list = extend_schema(
        methods=["GET"],
        summary="개설된 강습과정의 수업정보 목록",
        description="개설된 강습과정의 수업정보 목록 API. 강습과정이 개설되고 수업정보가 컨펌된 수업만 조회가능.",
    )

    sports_course_detail = extend_schema(
        methods=["GET"],
        summary="개설된 강습과정의 수업정보 상세",
        description="개설된 강습과정의 수업정보 상세 API. 강습과정이 개설되고 수업정보가 컨펌된 수업 상세 정보.",
    )

    courses_info = extend_schema(
        methods=["GET"],
        summary="Course list",
        description="Course 정보 API. sports의 중분류인 sports course 과정에 대한 정보. 현재 개설된 과정, 강사, 위치 정보",
    )

    class_product_list = extend_schema(
        methods=["GET"],
        summary="Class Product list",
        description="Class Product 정보 API. 개설된 과정 정보 목록.",
    )

    class_product_detail = extend_schema(
        methods=["GET"],
        summary="Class Product 상세정보",
        description="Class Product 상세정보 API. 개설된 과정 정보 상세. User는 class product를 통해 강사가 만든 강습 정보를 통해 강습을 선택하고 장소와 일정을 신청할 수 있다.",
    )

    instructor_list = extend_schema(
        methods=["GET"],
        summary="강습 가능한 강사 목록",
        description="강습 가능한 강사 목록 API. 강습 자격을 가진 강사 조회.",
    )

    location_list = extend_schema(
        methods=["GET"],
        summary="강습 가능한 지역 목록",
        description="강습 가능한 지역 목록 API. 강습이 진행 가능한 지역 조회.",
    )

    class_product_create = extend_schema(
        methods=["POST"],
        summary="Class Product 생성",
        description="Class Product 생성 API. 새로운 강습 과정을 생성합니다.",
        request=inline_serializer(
            name="ClassProductCreateSerializer",
            fields={
                "name": serializers.CharField(),
                "description": serializers.CharField(),
                "price": serializers.DecimalField(max_digits=10, decimal_places=2),
                "max_participants": serializers.IntegerField(),
                "images": serializers.ListField(child=serializers.ImageField()),
                "detail_images": serializers.ListField(child=serializers.ImageField()),
            },
        ),
    )

    class_product_update = extend_schema(
        methods=["PUT"],
        summary="Class Product 수정",
        description="Class Product 수정 API. 기존 강습 과정을 수정합니다.",
        request=inline_serializer(
            name="ClassProductUpdateSerializer",
            fields={
                "name": serializers.CharField(required=False),
                "description": serializers.CharField(required=False),
                "price": serializers.DecimalField(max_digits=10, decimal_places=2, required=False),
                "max_participants": serializers.IntegerField(required=False),
                "images": serializers.ListField(child=serializers.ImageField(), required=False),
                "detail_images": serializers.ListField(child=serializers.ImageField(), required=False),
            },
        ),
    )

    class_product_partial_update = extend_schema(
        methods=["PATCH"],
        summary="Class Product 부분 수정",
        description="Class Product 부분 수정 API. 기존 강습 과정의 일부 정보만 수정합니다.",
        request=inline_serializer(
            name="ClassProductPartialUpdateSerializer",
            fields={
                "name": serializers.CharField(required=False),
                "description": serializers.CharField(required=False),
                "price": serializers.DecimalField(max_digits=10, decimal_places=2, required=False),
                "max_participants": serializers.IntegerField(required=False),
                "images": serializers.ListField(child=serializers.ImageField(), required=False),
                "detail_images": serializers.ListField(child=serializers.ImageField(), required=False),
            },
        ),
    )

    class_product_delete = extend_schema(
        methods=["DELETE"],
        summary="Class Product 삭제",
        description="Class Product 삭제 API. 기존 강습 과정을 삭제합니다.",
    )
