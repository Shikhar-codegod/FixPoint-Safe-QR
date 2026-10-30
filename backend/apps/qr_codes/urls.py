from django.urls import path
from .views import UserQRCodeBadgesView, QRCodePublicResolveView

app_name = 'qr_codes'

urlpatterns = [
    path('', UserQRCodeBadgesView.as_view(), name='badges'),
    path('resolve/<str:code_identifier>/', QRCodePublicResolveView.as_view(), name='resolve-badge'),
]
