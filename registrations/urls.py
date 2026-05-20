from django.urls import path
from . import views

urlpatterns = [
    path("registrations/", views.registration_create, name="registration-create"),
    path("registrations/<int:pk>/confirm/", views.registration_confirm, name="registration-confirm"),
    path("registrations/<int:pk>/cancel/", views.registration_cancel, name="registration-cancel"),
    path("me/registrations/", views.my_registrations, name="my-registrations"),
    path("checkins/", views.checkin_create, name="checkin-create"),
    path("feedback/", views.feedback_create, name="feedback-create"),
]
