# TODO: 레벨 관련 정책 정리 필요
LEVEL_CHOICES = (
    (0, 'default 0'),
    (11, '프린이'),
    (12, '초급'),
    (13, '중급'),
    (14, '고급'),
)

GENDER_CHOICES = (
    ("M", "남성"),
    ("F", "여성"),
)


PAYMENT_TYPE_CHOICES = (
    ('course', '강습 결제'),
    ('class', '클래스 결제'),
)
    
PAYMENT_STATUS_CHOICES = (
    ('pending', '결제 대기'),
    ('paid', '결제 완료'),
    ('cancelled', '취소됨'),
    ('completed', '완료'),
)

COURCE_STATUS_CHOICES = (
    ('pending', '대기 중'),
    ('approved', '승인됨'),
    ('rejected', '거절됨'),
    ('completed', '완료됨'),
)

CLASS_STATUS_CHOICES = (
    ('pending', '결제 대기'),
    ('paid', '결제 완료'),
    ('cancelled', '취소됨'),
    ('completed', '수강 완료'),
)

PARTICIPATION_CHOICES = (
    ('lesson', '강습'),
    ('practice', '자율 연습'),
)