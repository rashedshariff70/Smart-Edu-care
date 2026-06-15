from django.urls import path
from . import views
from admin_app import views as admin_views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin_login/', admin_views.admin_login, name='admin_login'),
    path('admin_dash/', admin_views.admin_dash, name='admin_dash'),
    path('indexs/', views.indexs, name='indexs'), 
    path("admin_correct_data/", views.admin_correct_data, name="admin_correct_data"),
    path('admin_new_request/', views.university_reg_show, name='university_reg_show'),
    path('approve/<int:pk>/', views.admin_approve, name='admin_approve'),
    path('reject/<int:pk>/',  views.admin_reject,  name='admin_reject'),
    path('approved_show/',  views.approved_show,  name='approved_show'),
    path('send-correction-email/<int:pk>/',views.send_correction_email,name='send_correction_email'),
    path("student_data-send/", views.student_data_send, name="student_data_send"),
    path("admin-student-details/",views.admin_student_details_show,name="admin_student_details_show" ),
    path('college_data_upload/', views.college_data_upload, name='college_data_upload'),
    path('know_about_your_college/', views.know_about_your_college, name='know_about_your_college'),

]