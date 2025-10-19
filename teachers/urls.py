from django.urls import path

app_name = 'teachers'
from . import views

urlpatterns = [
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('review/<int:submission_id>/', views.review_submission, name='review_submission'),
]