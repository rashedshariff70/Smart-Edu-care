from student_app import views as student_views
from university_app import views as university_views
from admin_app import views as admin_views
from student_app import views
from django.contrib import admin
from django.urls import path, include 

urlpatterns = [
    
    path('admin/', admin.site.urls),
    path('admin_login/', admin_views.admin_login, name='admin_login'),
    path('admin_dash/', admin_views.admin_dash, name='admin_dash'),
    path('college_data_upload/', admin_views.college_data_upload, name='college_data_upload'),
    path('know_about_your_college/', admin_views.know_about_your_college, name='know_about_your_college'),
    

    path('student/', include('student_app.urls')),
    path("student_login/", views.student_login_view, name="student_login_valid"),
    path('student_register/', student_views.student_register, name='register'),
    path('student_ml_home/', student_views.student_ml_home, name='student_ml_home'),
    path('student_ml_upload_data/', student_views.student_ml_upload_data, name='student_ml_upload_data'),
    path('student_ml_view_models/', student_views.student_ml_view_models, name='student_ml_view_models'),
    path('student_ml_prediction/', student_views.student_ml_prediction, name='student_ml_prediction'),
    path('student_data_chat/', views.student_data_chat,     name='student_data_chat'),
    path('student_chat_room/',   views.student_chat_room,   name='student_chat_room'),
    path('student_chat_ask/',    views.student_chat_ask,    name='student_chat_ask'),
    path('student_chat_voice/',  views.student_chat_voice,  name='student_chat_voice'),
    path('student_chat_logout/', views.student_chat_logout, name='student_chat_logout'),
    path('parent_login/',  views.parent_login,   name='parent_login'),
    path('parent_data_chat/',     views.parent_data_chat,  name='parent_data_chat'),
    path('parent_chat_room/',    views.parent_chat_room,   name='parent_chat_room'),
    path('parent_chat_ask/',     views.parent_chat_ask,    name='parent_chat_ask'),
    path('parent_chat/voice/',   views.parent_chat_voice,  name='parent_chat_voice'),
    path('parent_chat_logout/',  views.parent_chat_logout, name='parent_chat_logout'),
    path("parent-chat/tts/", views.parent_chat_tts, name="parent_chat_tts"),
    path('parent_report_generate/', views.parent_report_generate, name='parent_report_generate'),


    path('university/', include('university_app.urls')),
    path('university_register/', university_views.university_register, name="university_reg_save"),
    path('university_reg_show/', university_views.university_reg_show, name="university_reg_show"),
    path("university_login/", university_views.university_login, name="university_login"),
    path("student_data_upload/", university_views.student_data_upload, name="student_data_upload"),

    path('', include('admin_app.urls')),  # Root URL → admin_app
]
