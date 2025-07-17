from django.urls import path
from . import views

urlpatterns = [
    # Frontend expected endpoints (using 'decks' instead of 'sets')
    path('decks/', views.FlashcardSetListCreateView.as_view(), name='flashcard-deck-list-create'),
    path('decks/<int:pk>/', views.FlashcardSetDetailView.as_view(), name='flashcard-deck-detail'),
    path('decks/<int:deck_id>/cards/', views.FlashcardListCreateView.as_view(), name='flashcard-list-create'),
    path('decks/<int:deck_id>/cards/<int:pk>/', views.FlashcardDetailView.as_view(), name='flashcard-detail'),
    path('decks/<int:deck_id>/study/', views.start_study_session, name='deck-study-session'),

    # Backward compatibility endpoints
    path('sets/', views.FlashcardSetListCreateView.as_view(), name='flashcard-set-list-create'),
    path('sets/<int:pk>/', views.FlashcardSetDetailView.as_view(), name='flashcard-set-detail'),
    path('sets/<int:set_id>/flashcards/', views.FlashcardListCreateView.as_view(), name='flashcard-list-create-old'),
    path('flashcards/<int:pk>/', views.FlashcardDetailView.as_view(), name='flashcard-detail-old'),

    # Additional endpoints
    path('review/', views.review_flashcard, name='review-flashcard'),
    path('stats/', views.flashcard_stats, name='flashcard-stats'),
    path('sessions/start/<int:set_id>/', views.start_study_session, name='start-study-session'),
    path('sessions/end/<int:session_id>/', views.end_study_session, name='end-study-session'),
    path('generate/', views.generate_flashcards_from_note, name='generate-flashcards'),
    path('generate-topic/', views.generate_flashcards_from_topic, name='generate-flashcards-topic'),
]
