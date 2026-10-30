from django.urls import path
from .views import UserProfileView, ResponderProfileView

app_name = 'profiles'

urlpatterns = [
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('responder/', ResponderProfileView.as_view(), name='responder-profile'),
]
