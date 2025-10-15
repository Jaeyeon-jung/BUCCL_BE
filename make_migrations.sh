#!/bin/bash
set -e # 오류 발생 시 즉시 중단

# --- 설정 변수 ---
DEV_IMAGE_NAME="backend_dev_im_tmp" # 개발 Dockerfile로 빌드할 이미지 이름
TEMP_CONTAINER_NAME="migration_temp_$(date +%s)" # 충돌 방지를 위한 임시 컨테이너 이름
# 마이그레이션 파일이 생성될 수 있는 앱 디렉토리 목록 (필요에 따라 추가/수정)
APP_DIRS=("buccl_user" "buccl_main")

# --- 스크립트 사용법 ---
# ./make_migrations.sh                # 모든 앱에 대해 마이그레이션 생성 시도
# ./make_migrations.sh <앱_이름>      # 특정 앱에 대해 마이그레이션 생성 시도

APP_NAME_ARG=$1

# --- 스크립트 종료 시 임시 컨테이너 정리 ---
cleanup() {
  echo "Cleaning up temporary container '$TEMP_CONTAINER_NAME'...'"
  # 컨테이너 중지 (오류 무시)
  docker stop $TEMP_CONTAINER_NAME > /dev/null 2>&1 || true
  # 컨테이너 삭제 (오류 무시)
  docker rm $TEMP_CONTAINER_NAME > /dev/null 2>&1 || true
  echo "Cleanup finished."
}
trap cleanup EXIT # 스크립트 종료 시(오류 포함) cleanup 함수 실행

# 1. 최신 코드로 개발 이미지 빌드
echo "Building development image '$DEV_IMAGE_NAME' with latest code..."
docker build -t $DEV_IMAGE_NAME -f Dockerfile.dev .
echo "Image build complete."

# 2. 임시 컨테이너 시작 (잠시 대기하도록 sleep 실행)
echo "Starting temporary container '$TEMP_CONTAINER_NAME'...'"
docker run -d --name $TEMP_CONTAINER_NAME --entrypoint sleep $DEV_IMAGE_NAME 60 # 60초 대기
echo "Temporary container started."

# 3. 실행 중인 임시 컨테이너 내부에서 makemigrations 실행
echo "Running makemigrations inside container..."
# 명령어 실행 (오류 발생 가능, 예를 들어 변경 사항 없을 때)
docker exec $TEMP_CONTAINER_NAME python manage.py makemigrations $APP_NAME_ARG || true
echo "makemigrations finished."

# 4. 생성된 마이그레이션 파일을 컨테이너에서 호스트로 복사
echo "Copying migration files from container to host..."
FILES_COPIED=false
for app_dir in "${APP_DIRS[@]}"; do
  HOST_PATH="./${app_dir}/migrations"
  CONTAINER_PATH="/app/${app_dir}/migrations"

  # 컨테이너 내부에 해당 migrations 디렉토리가 있는지 확인
  if docker exec $TEMP_CONTAINER_NAME ls $CONTAINER_PATH > /dev/null 2>&1; then
    echo "Copying migrations for ${app_dir}..."
    mkdir -p "$HOST_PATH"
    docker cp "${TEMP_CONTAINER_NAME}:${CONTAINER_PATH}/." "$HOST_PATH/"
    FILES_COPIED=true
  else
    : # 디렉토리 없으면 조용히 넘어감
  fi
done

if [ "$FILES_COPIED" = false ]; then
  echo "No migration files seem to have been generated or copied. Exiting."
  exit 0
fi
echo "Migration files copied to host."

# 5. Git 커밋 부분 제거됨
echo "----------------------------------------"
echo "Migration files have been created and copied to the host."
echo "Please review the files and commit them manually using Git."
echo "----------------------------------------"

# cleanup 함수가 trap에 의해 자동으로 실행됨
exit 0