from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # OpenAPI Schema
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Application APIs (versioned under /api/v1/)
    path('api/v1/', include('apps.common.urls', namespace='common')),
    path('api/v1/auth/', include('apps.accounts.urls', namespace='accounts')),
    path('api/v1/profiles/', include('apps.profiles.urls', namespace='profiles')),
    path('api/v1/qr/', include('apps.qr_codes.urls', namespace='qr_codes')),
    path('api/v1/contacts/', include('apps.contacts.urls', namespace='contacts')),
    path('api/v1/medical/', include('apps.medical.urls', namespace='medical')),
    path('api/v1/alerts/', include('apps.alerts.urls', namespace='alerts')),
    path('api/v1/notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('api/v1/incidents/', include('apps.incidents.urls', namespace='incidents')),
    path('api/v1/responders/', include('apps.responders.urls', namespace='responders')),
    path('api/v1/operations/', include('apps.operations.urls', namespace='operations')),
    path('api/v1/audit/', include('apps.audit.urls', namespace='audit')),
]
