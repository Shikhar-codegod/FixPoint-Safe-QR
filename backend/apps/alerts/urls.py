from django.urls import path
from .views import PublicAlertView, UserAlertsView

app_name = 'alerts'

urlpatterns = [
    path('public/<str:code_identifier>/', PublicAlertView.as_view(), name='public-alert'),
    path('', UserAlertsView.as_view(), name='alerts-list-create'),
]
