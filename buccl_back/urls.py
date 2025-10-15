"""buccl_back URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('server/admin/', admin.site.urls),
    path('server/buccl_user/', include('buccl_user.urls')),
    path('server/buccl_main/', include('buccl_main.urls')),
    path('server/buccl_lessons/', include('buccl_lessons.urls')),
]

# swagger 관련 URL 패턴 추가
if settings.ENV in ["dev", "prod"]: # TODO: 운영시 swagger url 노출시키지 않으려면 prod 제거
    urlpatterns += [
        path('server/schema/', SpectacularAPIView.as_view(api_version="api/v1"), name='schema'),
        path('server/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('server/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
