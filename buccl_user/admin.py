from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from .models import User, UserLevel, CertificateUpload
from django.utils import timezone

# 커스텀 AdminSite 생성
class SuperuserAdminSite(AdminSite):
    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser and request.user.is_staff

# User Admin 클래스 정의
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'user_email', 'level', 'is_active', 'is_staff', 'is_superuser', 'is_admin', 'date_joined')
    list_filter = ('level', 'is_active', 'is_staff', 'is_superuser', 'is_admin', 'date_joined')
    search_fields = ('user_id', 'name', 'user_email', 'hp')
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user_id', 'password', 'name', 'user_email', 'hp', 'user_birthday', 'user_gender')
        }),
        ('권한 정보', {
            'fields': ('level', 'is_active', 'is_staff', 'is_superuser', 'is_admin')
        }),
        ('이용약관 동의', {
            'fields': ('terms_accepted', 'age_confirmed', 'privacy_accepted')
        }),
        ('시스템 정보', {
            'fields': ('date_joined', 'last_login')
        }),
    )

# UserLevel Admin 클래스 정의
@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'description')
    search_fields = ('name', 'level')
    
    fieldsets = (
        ('레벨 정보', {
            'fields': ('name', 'level', 'description')
        }),
    )

# CertificateUpload Admin 클래스 정의
@admin.register(CertificateUpload)
class CertificateUploadAdmin(admin.ModelAdmin):
    list_display = ('user', 'certificate_name', 'certificate_preview', 'uploaded_at', 'is_approved')
    list_filter = ('is_approved', 'uploaded_at')
    search_fields = ('user__user_id', 'user__name', 'certificate_name')
    
    fieldsets = (
        ('인증서 정보', {
            'fields': ('user', 'certificate_name', 'certificate_file', 'certificate_preview')
        }),
        ('승인 정보', {
            'fields': ('is_approved', 'approved_by', 'rejection_reason')
        }),
        ('시스템 정보', {
            'fields': ('uploaded_at',)
        }),
    )
    
    readonly_fields = ('uploaded_at', 'certificate_preview')
    
    def certificate_preview(self, obj):
        if obj.certificate_file:
            return format_html('<a href="{}" target="_blank">인증서 보기</a>', obj.certificate_file.url)
        return "파일 없음"
    
    certificate_preview.short_description = '인증서 파일'
    
    actions = ['approve_certificates', 'reject_certificates']
    
    @admin.action(description='선택한 인증서 승인')
    def approve_certificates(self, request, queryset):
        updated = queryset.update(is_approved=True, approved_at=timezone.now(), approved_by=request.user)
        self.message_user(request, f'{updated}개의 인증서가 승인되었습니다.')
    
    @admin.action(description='선택한 인증서 거부')
    def reject_certificates(self, request, queryset):
        updated = queryset.update(is_approved=False, approved_at=None, approved_by=None)
        self.message_user(request, f'{updated}개의 인증서가 거부되었습니다.')