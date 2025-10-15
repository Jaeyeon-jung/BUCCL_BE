# Django 백엔드 배포 가이드

이 문서는 Django 백엔드 애플리케이션의 개발 및 운영 환경 배포 방법을 설명합니다.

## 필수 요구사항

- Docker
- Docker Compose
- Git

## Docker Compose를 사용한 배포 (권장)

### 개발 환경

```bash
# 개발 환경 실행
docker-compose up -d backend_dev

# 개발 환경 로그 확인
docker-compose logs -f backend_dev

# 개발 환경 중지
docker-compose down
```

### 운영 환경

```bash
# 운영 환경 실행
docker-compose up -d backend_prod

# 운영 환경 로그 확인
docker-compose logs -f backend_prod

# 운영 환경 중지
docker-compose down
```

### fixtures 로드 (필요시)

개발 환경 또는 운영 환경에서 fixtures 데이터를 로드하려면:

```bash
# 개발 환경에서 fixtures 로드
LOAD_FIXTURES=true docker-compose up -d --build backend_dev

# 운영 환경에서 fixtures 로드
LOAD_FIXTURES=true docker-compose up -d --build backend_prod
```

또는 docker-compose.yml 파일에서 `LOAD_FIXTURES=false`를 `LOAD_FIXTURES=true`로 변경한 후 컨테이너를 재시작하세요.

### 볼륨 마운트

- **개발 환경 / 운영 환경**: 볼륨 마운트가 사용되지 않습니다. Dockerfile 내부에서 파일이 복사됩니다.
- 코드 변경 시, 이미지를 다시 빌드해야 변경 사항이 컨테이너에 반영됩니다 (`docker-compose up -d --build <서비스명>`).

### 환경 변수 설정

Docker 파일에 환경 변수가 이미 설정되어 있습니다:
- 개발: `DJANGO_ENV=development` (Dockerfile.dev)
- 운영: `DJANGO_ENV=production` (Dockerfile.prod)

## Docker 단독 사용 배포

## 개발 환경 배포

### 1. 이미지 빌드

```bash
docker build -t backend_dev_im -f Dockerfile.dev .
```

### 2. 컨테이너 실행

```bash
# 기본 실행
docker run --name backend_dev -p 8001:8000 -d backend_dev_im

# fixtures 로드하며 실행
docker run --name backend_dev -p 8001:8000 -e LOAD_FIXTURES=true -d backend_dev_im
```

### 3. 로그 확인

```bash
docker logs -f backend_dev
```

## 운영 환경 배포

### 1. 이미지 빌드

```bash
docker build -t backend_prod_im -f Dockerfile.prod .
```

### 2. 컨테이너 실행

```bash
# 기본 실행
docker run --name backend_prod -p 8000:8000 -d backend_prod_im

# fixtures 로드하며 실행 (초기 배포 시)
docker run --name backend_prod -p 8000:8000 -e LOAD_FIXTURES=true -d backend_prod_im
```

### 3. 로그 확인

```bash
docker logs -f backend_prod
```

## 환경 변수

### 기본 환경 변수

각 환경의 설정은 다음 파일에 정의되어 있습니다:
- 개발: `.env.dev`
- 운영: `.env.prod`

### 컨테이너 실행 시 환경 변수

- `LOAD_FIXTURES=true`: fixtures 데이터를 로드합니다 (최초 배포 또는 테스트 데이터 필요 시)
- `DJANGO_ENV`: 개발(`development`) 또는 운영(`production`) 환경 설정 (Dockerfile에서 기본 설정됨)

## 마이그레이션 및 DB 관리

마이그레이션은 컨테이너 시작 시 자동으로 실행됩니다. 수동으로 실행하려면:

```bash
# 개발 환경
docker exec -it backend_dev python manage.py migrate

# 운영 환경
docker exec -it backend_prod python manage.py migrate
```

## 기타 유용한 명령어

### 컨테이너 관리

```bash
# 컨테이너 중지
docker stop backend_dev
docker stop backend_prod

# 컨테이너 재시작
docker restart backend_dev
docker restart backend_prod

# 컨테이너 삭제 (중지 후)
docker rm backend_dev
docker rm backend_prod
```

### Django 관리 명령어

```bash
# Django 관리자 생성 (개발)
docker exec -it backend_dev python manage.py createsuperuser

# Django 관리자 생성 (운영)
docker exec -it backend_prod python manage.py createsuperuser

# Django 쉘 접근 (개발)
docker exec -it backend_dev python manage.py shell

# 정적 파일 수집 (운영)
docker exec -it backend_prod python manage.py collectstatic --noinput
```

### shell_plus 실행 명령어

```bash
# 컨테이너 밖에서 실행시
docker-compose exec backend_dev python manage.py shell_plus

# 컨테이너 안에서 실행시
docker-compose exec backend_dev /bin/bash
root@92bf00d1dc57:/app$ python manage.py shell_plus
```

## 트러블슈팅

### DB 연결 문제

외부 DB 서버 접근 권한이 올바르게 설정되었는지 확인:

```sql
GRANT ALL PRIVILEGES ON dbdeeps_dev.* TO 'moddy5000'@'%';
FLUSH PRIVILEGES;
```

### 마이그레이션 충돌

마이그레이션 문제 발생 시 수동으로 마이그레이션 확인:

```bash
# 마이그레이션 상태 확인
docker exec -it backend_dev python manage.py showmigrations

# 특정 앱 마이그레이션 실행
docker exec -it backend_dev python manage.py migrate <app_name>
```

## API 문서화 관련

### drf-spectacular 관련 문서
- https://drf-spectacular.readthedocs.io/en/latest/readme.html

### URL
buccl_back/urls.py 참고
- schema : server/schema/
- swagger ui : server/schema/swagger
- redoc : server/schema/redoc


## TC(Test Code) 관련
모든 tests.py test_*.py *_tests.py 형식 파일 실행
```bash
# -rA 옵션은 상세 테스트 로그
docker-compose exec backend_dev pytest -rA
```

- 참고문서: https://pytest-django.readthedocs.io/en/latest/usage.html#basic-usage