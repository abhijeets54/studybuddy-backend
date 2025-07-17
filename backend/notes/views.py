from rest_framework import generics, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Note, Subject, Tag
from .serializers import NoteSerializer, NoteListSerializer, SubjectSerializer, TagSerializer


class NoteListCreateView(generics.ListCreateAPIView):
    """List all notes for the authenticated user or create a new note"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject', 'difficulty', 'is_favorite']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-updated_at']

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user).select_related('subject').prefetch_related('tags')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NoteListSerializer
        return NoteSerializer


class NoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a specific note"""
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user).select_related('subject').prefetch_related('tags')


class SubjectListCreateView(generics.ListCreateAPIView):
    """List all subjects or create a new subject"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering = ['name']


class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a specific subject"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]


class TagListCreateView(generics.ListCreateAPIView):
    """List all tags or create a new tag"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_notes_stats(request):
    """Get statistics about user's notes"""
    user_notes = Note.objects.filter(user=request.user)

    stats = {
        'total_notes': user_notes.count(),
        'favorite_notes': user_notes.filter(is_favorite=True).count(),
        'notes_by_difficulty': {
            'easy': user_notes.filter(difficulty='easy').count(),
            'medium': user_notes.filter(difficulty='medium').count(),
            'hard': user_notes.filter(difficulty='hard').count(),
        },
        'notes_by_subject': {}
    }

    # Get notes count by subject
    subjects = Subject.objects.all()
    for subject in subjects:
        count = user_notes.filter(subject=subject).count()
        if count > 0:
            stats['notes_by_subject'][subject.name] = count

    return Response(stats)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_notes_with_ai(request):
    """Generate notes using AI based on topic and optional description/guidelines"""
    from studybuddy.ai_service import ai_service

    topic = request.data.get('topic')
    description = request.data.get('description', '')
    guidelines = request.data.get('guidelines', '')
    subject_name = request.data.get('subject', '') or request.data.get('subject_name', '')
    difficulty = request.data.get('difficulty', 'medium')

    if not topic:
        return Response({'error': 'Topic is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Generate notes content using AI
        notes_content = ai_service.generate_notes(
            topic=topic,
            description=description,
            guidelines=guidelines
        )

        # Get or create subject if provided
        subject = None
        if subject_name.strip():
            subject, created = Subject.objects.get_or_create(
                name=subject_name.strip(),
                defaults={'description': f'Subject for {subject_name.strip()}'}
            )

        # Create the note
        note = Note.objects.create(
            title=f"AI Generated Notes: {topic}",
            content=notes_content,
            user=request.user,
            subject=subject,
            difficulty=difficulty
        )

        return Response(NoteSerializer(note).data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': f'Failed to generate notes: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
