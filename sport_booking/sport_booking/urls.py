"""
URL configuration for sport_booking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from reservations import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/reservations/', views.create_reservation, name='create-reservation'),
    path('api/availability/', views.check_availability, name='check-availability'),
    path(
        'api/reservations/<int:reservation_id>/confirm/',
        views.confirm_reservation,
        name='confirm-reservation',
    ),
    path(
        'api/reservations/<int:reservation_id>/approve/',
        views.approve_reservation,
        name='approve-reservation',
    ),
    path(
        'api/reservations/<int:reservation_id>/cancel/',
        views.cancel_reservation,
        name='cancel-reservation',
    ),
]
