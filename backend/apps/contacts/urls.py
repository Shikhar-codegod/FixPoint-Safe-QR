from django.urls import path
from .views import (
    EmergencyContactsView,
    EmergencyContactDetailView,
    ContactConsentRequestView,
    ContactConsentWithdrawView,
    PublicContactConsentView,
)

app_name = 'contacts'

urlpatterns = [
    path('', EmergencyContactsView.as_view(), name='contacts-list-create'),
    path('consent/<str:token>/', PublicContactConsentView.as_view(), name='public-contact-consent'),
    path('<uuid:contact_id>/', EmergencyContactDetailView.as_view(), name='contact-detail'),
    path('<uuid:contact_id>/consent/request/', ContactConsentRequestView.as_view(), name='contact-consent-request'),
    path('<uuid:contact_id>/consent/withdraw/', ContactConsentWithdrawView.as_view(), name='contact-consent-withdraw'),
]
