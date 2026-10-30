from django.urls import path
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CurrentUserView,
    ResponderVerificationView,
    UnverifiedRespondersListView,
)

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('responders/pending/', UnverifiedRespondersListView.as_view(), name='pending_responders'),
    path('responders/<uuid:user_id>/verify/', ResponderVerificationView.as_view(), name='verify_responder'),
]
