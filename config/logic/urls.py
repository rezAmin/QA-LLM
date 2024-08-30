from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('ask_question/', views.ask_question, name='submit_question'),
    path('get_content/', views.get_content, name='get_content'),
    path('get_question_history/', views.get_question_history, name='get_question_history'),
    path('get_answer/', views.get_answer, name='get_answer'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
]