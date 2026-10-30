from django.urls import path
from .views import OperationsLogView

app_name = 'operations'

urlpatterns = [
    path('log/', OperationsLogView.as_view(), name='operations-log'),
]
