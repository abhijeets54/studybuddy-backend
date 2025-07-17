from rest_framework import generics, filters, status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import FlashcardSet, Flashcard, FlashcardProgress, StudySession
from .serializers import (
    FlashcardSetSerializer, FlashcardSetListSerializer, FlashcardSetCreateSerializer,
    FlashcardSerializer, FlashcardCreateSerializer, FlashcardProgressSerializer,
    StudySessionSerializer, FlashcardReviewSerializer
)
from analytics.utils import track_flashcard_session


class FlashcardSetListCreateView(generics.ListCreateAPIView):
    """List all flashcard sets for the authenticated user or create a new set"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject', 'is_public']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-updated_at']

    def get_queryset(self):
        return FlashcardSet.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        ).select_related('subject')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FlashcardSetListSerializer
        return FlashcardSetCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        # Return the full object with ID
        response_serializer = FlashcardSetSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class FlashcardSetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a specific flashcard set"""
    serializer_class = FlashcardSetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FlashcardSet.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        ).select_related('subject').prefetch_related('flashcards')


class FlashcardListCreateView(generics.ListCreateAPIView):
    """List flashcards in a set or create a new flashcard"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FlashcardSerializer
        return FlashcardCreateSerializer

    def get_queryset(self):
        # Handle both 'set_id' and 'deck_id' for backward compatibility
        set_id = self.kwargs.get('set_id') or self.kwargs.get('deck_id')
        return Flashcard.objects.filter(
            flashcard_set_id=set_id,
            flashcard_set__user=self.request.user
        ).order_by('order')

    def perform_create(self, serializer):
        # Handle both 'set_id' and 'deck_id' for backward compatibility
        set_id = self.kwargs.get('set_id') or self.kwargs.get('deck_id')
        try:
            flashcard_set = FlashcardSet.objects.get(id=set_id, user=self.request.user)
            serializer.save(flashcard_set=flashcard_set)
        except FlashcardSet.DoesNotExist:
            raise serializers.ValidationError("Flashcard set not found")


class FlashcardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a specific flashcard"""
    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # If deck_id is provided, filter by deck as well
        deck_id = self.kwargs.get('deck_id')
        queryset = Flashcard.objects.filter(flashcard_set__user=self.request.user)
        if deck_id:
            queryset = queryset.filter(flashcard_set_id=deck_id)
        return queryset


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_flashcard(request):
    """Record a flashcard review"""
    serializer = FlashcardReviewSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    flashcard_id = serializer.validated_data['flashcard_id']
    difficulty = serializer.validated_data['difficulty']

    try:
        flashcard = Flashcard.objects.get(id=flashcard_id)
    except Flashcard.DoesNotExist:
        return Response({'error': 'Flashcard not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get or create progress record
    progress, created = FlashcardProgress.objects.get_or_create(
        user=request.user,
        flashcard=flashcard,
        defaults={'difficulty': difficulty}
    )

    # Update progress based on difficulty
    progress.difficulty = difficulty
    progress.review_count += 1
    progress.last_reviewed = timezone.now()

    # Calculate next review date based on spaced repetition
    if difficulty == 'again':
        progress.next_review = timezone.now() + timedelta(minutes=10)
        progress.is_mastered = False
    elif difficulty == 'hard':
        progress.next_review = timezone.now() + timedelta(days=1)
        progress.is_mastered = False
    elif difficulty == 'good':
        progress.next_review = timezone.now() + timedelta(days=3)
        if progress.review_count >= 5:
            progress.is_mastered = True
    elif difficulty == 'easy':
        progress.next_review = timezone.now() + timedelta(days=7)
        if progress.review_count >= 3:
            progress.is_mastered = True

    progress.save()

    return Response(FlashcardProgressSerializer(progress).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flashcard_stats(request):
    """Get flashcard statistics for the authenticated user"""
    user_progress = FlashcardProgress.objects.filter(user=request.user)
    user_sessions = StudySession.objects.filter(user=request.user)

    stats = {
        'total_flashcards_studied': user_progress.count(),
        'flashcards_mastered': user_progress.filter(is_mastered=True).count(),
        'total_study_sessions': user_sessions.count(),
        'total_study_time': sum(session.session_duration for session in user_sessions),
        'average_session_duration': user_sessions.aggregate(
            avg_duration=Avg('session_duration')
        )['avg_duration'] or 0,
        'flashcards_due_for_review': user_progress.filter(
            next_review__lte=timezone.now()
        ).count(),
        'recent_sessions': []
    }

    # Get recent study sessions
    recent_sessions = user_sessions.select_related('flashcard_set').order_by('-started_at')[:5]
    stats['recent_sessions'] = [
        {
            'flashcard_set_title': session.flashcard_set.title,
            'cards_studied': session.cards_studied,
            'cards_mastered': session.cards_mastered,
            'session_duration': session.session_duration,
            'started_at': session.started_at
        }
        for session in recent_sessions
    ]

    return Response(stats)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_study_session(request, set_id):
    """Start a new study session for a flashcard set"""
    try:
        flashcard_set = FlashcardSet.objects.get(
            id=set_id,
            user=request.user
        )
    except FlashcardSet.DoesNotExist:
        return Response({'error': 'Flashcard set not found'}, status=status.HTTP_404_NOT_FOUND)

    session = StudySession.objects.create(
        user=request.user,
        flashcard_set=flashcard_set
    )

    return Response(StudySessionSerializer(session).data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def end_study_session(request, session_id):
    """End a study session and update statistics"""
    try:
        session = StudySession.objects.get(id=session_id, user=request.user)
    except StudySession.DoesNotExist:
        return Response({'error': 'Study session not found'}, status=status.HTTP_404_NOT_FOUND)

    # Update session data from request
    session.cards_studied = request.data.get('cards_studied', session.cards_studied)
    session.cards_mastered = request.data.get('cards_mastered', session.cards_mastered)
    session.session_duration = request.data.get('session_duration', session.session_duration)
    session.completed_at = timezone.now()
    session.save()

    # Update analytics tracking
    track_flashcard_session(
        user=request.user,
        flashcard_set=session.flashcard_set,
        cards_studied=session.cards_studied,
        session_duration_seconds=session.session_duration
    )

    return Response(StudySessionSerializer(session).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_flashcards_from_note(request):
    """Generate flashcards from a note using AI"""
    from studybuddy.ai_service import ai_service
    from notes.models import Note

    note_id = request.data.get('note_id')
    num_cards = request.data.get('num_cards', 10)

    if not note_id:
        return Response({'error': 'note_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        note = Note.objects.get(id=note_id, user=request.user)
    except Note.DoesNotExist:
        return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Generate flashcards using AI
        flashcards_data = ai_service.generate_flashcards(
            note_content=note.content,
            note_title=note.title,
            num_cards=num_cards
        )

        # Create flashcard set
        flashcard_set = FlashcardSet.objects.create(
            title=f"Flashcards: {note.title}",
            description=f"AI-generated flashcards from note: {note.title}",
            user=request.user,
            note=note,
            subject=note.subject
        )

        # Create flashcards
        for i, card_data in enumerate(flashcards_data):
            Flashcard.objects.create(
                flashcard_set=flashcard_set,
                front_text=card_data['front_text'],
                back_text=card_data['back_text'],
                hint=card_data.get('hint', ''),
                order=i + 1
            )

        return Response(FlashcardSetSerializer(flashcard_set).data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_flashcards_from_topic(request):
    """Generate flashcards directly from a topic using AI without creating a note"""
    from studybuddy.ai_service import ai_service
    from notes.models import Subject

    topic = request.data.get('topic')
    description = request.data.get('description', '')
    num_cards = request.data.get('num_cards', 10)
    subject_name = request.data.get('subject_name', '')

    if not topic or not topic.strip():
        return Response({'error': 'topic is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Create content from topic and description
        content = description if description.strip() else f"Study material for: {topic}"

        # Generate flashcards using AI
        flashcards_data = ai_service.generate_flashcards(
            note_content=content,
            note_title=topic,
            num_cards=num_cards
        )

        # Handle subject if provided
        subject = None
        if subject_name and subject_name.strip():
            subject, created = Subject.objects.get_or_create(
                name=subject_name.strip(),
                defaults={'description': f'Subject for {subject_name.strip()}'}
            )

        # Create flashcard set without linking to a note
        flashcard_set = FlashcardSet.objects.create(
            title=topic,
            description=f"AI-generated flashcards for: {topic}",
            user=request.user,
            note=None,  # No note association
            subject=subject
        )

        # Create flashcards
        for i, card_data in enumerate(flashcards_data):
            Flashcard.objects.create(
                flashcard_set=flashcard_set,
                front_text=card_data['front_text'],
                back_text=card_data['back_text'],
                hint=card_data.get('hint', ''),
                order=i + 1
            )

        return Response(FlashcardSetSerializer(flashcard_set).data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error generating flashcards from topic: {e}")
        return Response({'error': 'Failed to generate flashcards'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
