from django.urls import path
from . import views

urlpatterns = [
    path('', views.NoteListCreateView.as_view(), name='note-list-create'),
    path('<int:pk>/', views.NoteDetailView.as_view(), name='note-detail'),
    path('subjects/', views.SubjectListCreateView.as_view(), name='subject-list-create'),
    path('subjects/<int:pk>/', views.SubjectDetailView.as_view(), name='subject-detail'),
    path('tags/', views.TagListCreateView.as_view(), name='tag-list-create'),
    path('stats/', views.user_notes_stats, name='notes-stats'),
    path('generate-ai/', views.generate_notes_with_ai, name='generate-notes-ai'),
]
