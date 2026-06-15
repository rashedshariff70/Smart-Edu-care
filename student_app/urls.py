from django.urls import path
from . import views


urlpatterns = [


    path('student_register/', views.student_register, name='student_register'),


    # STUDENT ML ROUTES
    
    path("student_login/", views.student_login_view, name="student_login_valid"),
    path('student_chat_room/',   views.student_chat_room,   name='student_chat_room'),
    path('student_chat_ask/',    views.student_chat_ask,    name='student_chat_ask'),
    path('student_chat_voice/',  views.student_chat_voice,  name='student_chat_voice'),
    path('student_chat_logout/', views.student_chat_logout, name='student_chat_logout'),
    path('parent_login/',           views.parent_login,           name='parent_login'),
    path('parent_chat_logout/',     views.parent_chat_logout,     name='parent_chat_logout'),
    # ── Chat room ──
    path('parent_chat_room/',       views.parent_chat_room,       name='parent_chat_room'),
    # ── Chat API endpoints ──
    path('parent_chat_ask/',        views.parent_chat_ask,        name='parent_chat_ask'),
    path('parent_chat/voice/',      views.parent_chat_voice,      name='parent_chat_voice'),
    path('parent-chat/tts/',        views.parent_chat_tts,        name='parent_chat_tts'),
    

    path('parent_report_generate/', views.parent_report_generate, name='parent_report_generate'),

 


]


