from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('chat', views.chat, name='chat'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('chat_history', views.chat_history, name='chat_history'),
    path('logout', views.logout, name='logout'),
    path('settings/', views.settings, name='settings'),
    path('diagnose/', views.diagnose, name='diagnose'),
    path('get-chat-history/', views.get_chat_history, name='get_chat_history'),
     
    
    # Forgot Password URLS
    path('forgot_password/', auth_views.PasswordResetView.as_view(template_name='forgot_password.html'), name='forgot_password'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

]
