from django.urls import path
from .views import UserAlertsView

app_name = 'alerts'

urlpatterns = [
    path('', UserAlertsView.as_view(), name='alerts-list-create'),
]
