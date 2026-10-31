from django.urls import path
from .views import ResponderDispatchListView, ResponderDispatchDetailView

app_name = 'responders'

urlpatterns = [
    path('dispatches/', ResponderDispatchListView.as_view(), name='responder-dispatches'),
    path('dispatches/<uuid:dispatch_id>/', ResponderDispatchDetailView.as_view(), name='responder-dispatch-detail'),
]

