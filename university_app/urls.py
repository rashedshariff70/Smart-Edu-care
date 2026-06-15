from django.urls import path
from . import views

urlpatterns = [
    path('', views.register_view, name="university_register"),
    path('university_register/', views.university_register, name="university_reg_save"),
    path('university_reg_show/', views.university_reg_show, name="university_reg_show"),
    path("university_login/", views.university_login, name="university_login"),
    path("student_data_upload/", views.student_data_upload, name="student_data_upload"),

]
