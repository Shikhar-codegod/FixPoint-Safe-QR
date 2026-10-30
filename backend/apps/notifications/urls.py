from django.urls import path
from .views import UserNotificationsView

app_name = 'notifications'

urlpatterns = [
    path('', UserNotificationsView.as_view(), name='notifications-list'),
]
