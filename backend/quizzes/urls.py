from django.urls import path
from . import views

urlpatterns = [
    path('', views.QuizListCreateView.as_view(), name='quiz-list-create'),
    path('<int:pk>/', views.QuizDetailView.as_view(), name='quiz-detail'),
    path('attempts/', views.QuizAttemptListView.as_view(), name='quiz-attempts'),
    path('submit/', views.submit_quiz, name='submit-quiz'),
    path('stats/', views.quiz_stats, name='quiz-stats'),
    path('generate/', views.generate_quiz_from_note, name='generate-quiz'),
    path('generate-topic/', views.generate_quiz_from_topic, name='generate-quiz-topic'),
]
