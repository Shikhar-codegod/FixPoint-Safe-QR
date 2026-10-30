from django.urls import path
from .views import ResponderDispatchListView

app_name = 'responders'

urlpatterns = [
    path('dispatches/', ResponderDispatchListView.as_view(), name='responder-dispatches'),
]
