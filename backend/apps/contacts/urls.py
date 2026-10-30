from django.urls import path
from .views import EmergencyContactsView, EmergencyContactDetailView

app_name = 'contacts'

urlpatterns = [
    path('', EmergencyContactsView.as_view(), name='contacts-list-create'),
    path('<uuid:contact_id>/', EmergencyContactDetailView.as_view(), name='contact-detail'),
]
