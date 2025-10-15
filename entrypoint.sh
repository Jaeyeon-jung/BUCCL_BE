#!/bin/bash
set -e

# 마이그레이션 실행
echo "Running migrations..."
python manage.py migrate

# 환경에 따라 fixture 로드 여부 결정
if [ "$DJANGO_ENV" = "development" ] || [ "$LOAD_FIXTURES" = "true" ]; then
  echo "Loading fixtures..."
  # python manage.py loaddata buccl_main/fixtures/initial_locations.json && \
  # python manage.py loaddata buccl_main/fixtures/initial_sports.json && \
  # python manage.py loaddata buccl_main/fixtures/initial_course_types.json
fi

# 환경에 따라 서버 실행
if [ "$DJANGO_ENV" = "production" ]; then
  echo "Starting production server with gunicorn..."
  gunicorn --bind 0.0.0.0:8000 buccl_back.wsgi:application
else
  echo "Starting development server..."
  python manage.py runserver 0.0.0.0:8000
fi