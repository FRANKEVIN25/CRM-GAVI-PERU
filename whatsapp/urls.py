from django.urls import path

from . import views

app_name = "whatsapp"

urlpatterns = [
    path("twilio/entrante/", views.twilio_entrante, name="twilio_entrante"),
    path("twilio/estado/", views.twilio_estado, name="twilio_estado"),
]
