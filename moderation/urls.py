from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='mod_login'),
    path('logout/', views.logout_view, name='mod_logout'),
    path('', views.dashboard_view, name='mod_dashboard'),
    path('artists/', views.artist_list_view, name='mod_artists'),
    path('artists/<int:user_id>/toggle/', views.toggle_artist_view, name='mod_toggle_artist'),
    path('artists/<int:user_id>/delete/', views.delete_artist_view, name='mod_delete_artist'),
    path('clients/', views.client_list_view, name='mod_clients'),
    path('clients/<int:user_id>/toggle/', views.toggle_client_view, name='mod_toggle_client'),
    path('clients/<int:user_id>/delete/', views.delete_client_view, name='mod_delete_client'),
    path('content/', views.content_review_view, name='mod_content'),
    path('content/<int:message_id>/action/', views.content_action_view, name='mod_content_action'),
    path('negotiations/', views.negotiations_view, name='mod_negotiations'),
    path('negotiations/<int:job_id>/delete/', views.delete_job_request_view, name='mod_delete_job'),
    path('messages/<int:message_id>/delete-image/', views.delete_message_image_view, name='mod_delete_image'),
]
