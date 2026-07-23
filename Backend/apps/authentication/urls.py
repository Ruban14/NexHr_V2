"""Authentication API URL routes."""

from __future__ import annotations

from django.urls import path

from apps.authentication import views

app_name = 'authentication'

urlpatterns = [
    path('register', views.RegisterView.as_view(), name='register'),
    path('login', views.LoginView.as_view(), name='login'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('refresh', views.RefreshView.as_view(), name='refresh'),
    path('forgot-password', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password', views.ResetPasswordView.as_view(), name='reset-password'),
    path('verify-email', views.VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification', views.ResendVerificationView.as_view(), name='resend-verification'),
    path('me', views.MeView.as_view(), name='me'),
]
