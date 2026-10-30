from django.urls import path
from .views import MedicalProfileView

app_name = 'medical'

urlpatterns = [
    path('me/', MedicalProfileView.as_view(), name='medical-profile'),
]
