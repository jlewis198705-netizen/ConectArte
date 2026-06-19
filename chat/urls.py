from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # API endpoints
    path('api/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('api/requests/', views.list_job_requests, name='list_job_requests'),
    path('api/requests/create/', views.create_job_request, name='create_job_request'),
    path('api/requests/<int:pk>/classify/', views.trigger_ai_classification, name='trigger_ai_classification'),
    path('api/requests/<int:pk>/complete/', views.complete_job_request, name='complete_job_request'),
    path('api/requests/<int:pk>/messages/', views.get_messages, name='get_messages'),
    path('api/requests/<int:pk>/messages/send/', views.send_message, name='send_message'),
    path('api/requests/<int:pk>/before-after/', views.get_before_after, name='get_before_after'),
]
