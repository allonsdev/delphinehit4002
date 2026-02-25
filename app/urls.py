from django.urls import path
from app import views

urlpatterns = [
    path('scan-qr/', views.scan_qr, name='scan_qr'),
]
