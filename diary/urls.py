from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('calendar', views.calendar, name='calendar'),
    path('entry/<str:date>/', views.entry_view, name='entry_view'),
    path('events/', views.diary_events, name='diary_events'),
    path('answers/<str:date>/', views.daily_answers_view, name='daily_answers'),
    path('answers/<str:date>/export/txt/', views.export_answers_txt, name='export_answers_txt'),
    path('answers/<str:date>/export/pdf/', views.export_answers_pdf, name='export_answers_pdf'),
    path('answers/export/all/pdf/', views.export_all_answers_pdf, name='export_all_answers_pdf'),
    path('entries/export/all/pdf/', views.export_all_entries_pdf, name='export_all_entries_pdf'),
    path('entry/<str:date>/delete/', views.delete_entry, name='delete_entry'),
    path('trash/', views.trash_view, name='trash'),
    path('test/', views.test, name='test'),
    path('restore/<str:date>/', views.restore_entry, name='restore_entry'),
    path('permanent-delete/<str:date>/', views.permanent_delete_entry, name='permanent_delete_entry'),
    path('export-today-answers/', views.export_today_answers_pdf, name='export_today_answers_pdf'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('profile/', views.profile_view, name='profile'),
    path('delete-image/<str:date>/', views.delete_image_entry, name='delete_image_entry'),
    path('upload-profile-image/', views.upload_profile_image, name='upload_profile_image'),
    path('reset-superuser/', views.reset_superuser_data, name='reset_superuser'),

    # authentication
    path('login/', auth_views.LoginView.as_view(template_name='diary/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('my-entries/', views.my_entries_view, name='my_entries'),
]
