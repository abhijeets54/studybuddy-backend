from rest_framework import generics, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Max
from .models import Quiz, Question, Choice, QuizAttempt, UserAnswer
from .serializers import (
    QuizSerializer, QuizListSerializer, QuizCreateSerializer,
    QuizAttemptSerializer, QuizSubmissionSerializer
)
from analytics.utils import track_quiz_completion


class QuizListCreateView(generics.ListCreateAPIView):
    """List all quizzes for the authenticated user or create a new quiz"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject', 'difficulty']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user).select_related('subject')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return QuizListSerializer
        return QuizCreateSerializer


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a specific quiz"""
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user).select_related('subject').prefetch_related(
            'questions__choices'
        )


class QuizAttemptListView(generics.ListAPIView):
    """List all quiz attempts for the authenticated user"""
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['quiz']
    ordering_fields = ['completed_at', 'score']
    ordering = ['-completed_at']

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user).select_related('quiz')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz(request):
    """Submit quiz answers and calculate score"""
    serializer = QuizSubmissionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    quiz_id = serializer.validated_data['quiz_id']
    answers = serializer.validated_data['answers']
    time_taken = serializer.validated_data['time_taken']

    try:
        quiz = Quiz.objects.get(id=quiz_id, user=request.user)
    except Quiz.DoesNotExist:
        return Response({'error': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)

    # Create quiz attempt
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        total_questions=quiz.questions.count(),
        time_taken=time_taken,
        score=0,  # Will be calculated
        correct_answers=0  # Will be calculated
    )

    correct_count = 0
    total_questions = 0

    # Process each answer
    for answer_data in answers:
        question_id = answer_data['question_id']
        choice_id = answer_data['choice_id']

        try:
            question = Question.objects.get(id=question_id, quiz=quiz)
            choice = Choice.objects.get(id=choice_id, question=question)

            is_correct = choice.is_correct
            if is_correct:
                correct_count += 1

            UserAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_choice=choice,
                is_correct=is_correct
            )
            total_questions += 1

        except (Question.DoesNotExist, Choice.DoesNotExist):
            continue

    # Calculate and update score
    if total_questions > 0:
        score = (correct_count / total_questions) * 100
        attempt.score = round(score, 2)
        attempt.correct_answers = correct_count
        attempt.total_questions = total_questions
        attempt.save()

        # Update analytics tracking
        track_quiz_completion(request.user, attempt)

        # Update user profile stats
        try:
            profile = request.user.profile
            profile.total_quizzes_taken += 1
            profile.save()
        except AttributeError:
            # Create profile if it doesn't exist
            from accounts.models import UserProfile
            profile = UserProfile.objects.create(
                user=request.user,
                total_quizzes_taken=1
            )

    return Response(QuizAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_stats(request):
    """Get quiz statistics for the authenticated user"""
    user_attempts = QuizAttempt.objects.filter(user=request.user)

    stats = {
        'total_quizzes_taken': user_attempts.count(),
        'average_score': user_attempts.aggregate(avg_score=Avg('score'))['avg_score'] or 0,
        'best_score': user_attempts.aggregate(max_score=Max('score'))['max_score'] or 0,
        'total_time_spent': sum(attempt.time_taken for attempt in user_attempts),
        'quizzes_by_difficulty': {},
        'recent_attempts': []
    }

    # Get quiz counts by difficulty
    from django.db.models import Count
    difficulty_stats = user_attempts.values('quiz__difficulty').annotate(
        count=Count('id'),
        avg_score=Avg('score')
    )

    for stat in difficulty_stats:
        difficulty = stat['quiz__difficulty']
        stats['quizzes_by_difficulty'][difficulty] = {
            'count': stat['count'],
            'average_score': round(stat['avg_score'], 2) if stat['avg_score'] else 0
        }

    # Get recent attempts
    recent_attempts = user_attempts.select_related('quiz').order_by('-completed_at')[:5]
    stats['recent_attempts'] = [
        {
            'quiz_title': attempt.quiz.title,
            'score': attempt.score,
            'completed_at': attempt.completed_at,
            'time_taken': attempt.time_taken
        }
        for attempt in recent_attempts
    ]

    return Response(stats)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_quiz_from_note(request):
    """Generate a quiz from a note using AI"""
    from studybuddy.ai_service import ai_service
    from notes.models import Note

    note_id = request.data.get('note_id')
    num_questions = request.data.get('num_questions', 5)
    difficulty = request.data.get('difficulty', 'medium')

    if not note_id:
        return Response({'error': 'note_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        note = Note.objects.get(id=note_id, user=request.user)
    except Note.DoesNotExist:
        return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Generate questions using AI
        questions_data = ai_service.generate_quiz_questions(
            note_content=note.content,
            note_title=note.title,
            num_questions=num_questions,
            difficulty=difficulty
        )

        # Create quiz
        quiz = Quiz.objects.create(
            title=f"Quiz: {note.title}",
            description=f"AI-generated quiz from note: {note.title}",
            user=request.user,
            note=note,
            subject=note.subject,
            difficulty=difficulty,
            total_questions=len(questions_data)
        )

        # Create questions and choices
        for i, question_data in enumerate(questions_data):
            question = Question.objects.create(
                quiz=quiz,
                question_text=question_data['question_text'],
                explanation=question_data.get('explanation', ''),
                order=i + 1
            )

            for j, choice_data in enumerate(question_data['choices']):
                Choice.objects.create(
                    question=question,
                    choice_text=choice_data['text'],
                    is_correct=choice_data['is_correct'],
                    order=j + 1
                )

        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_quiz_from_topic(request):
    """Generate a quiz from just a topic using AI"""
    from studybuddy.ai_service import ai_service

    topic = request.data.get('topic')
    num_questions = request.data.get('num_questions', 5)
    difficulty = request.data.get('difficulty', 'medium')
    subject_name = request.data.get('subject', '') or request.data.get('subject_name', '')

    if not topic:
        return Response({'error': 'topic is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Generate questions using AI
        questions_data = ai_service.generate_quiz_from_topic(
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty
        )

        # Get or create subject if provided
        subject = None
        if subject_name.strip():
            from notes.models import Subject
            subject, created = Subject.objects.get_or_create(
                name=subject_name.strip(),
                defaults={'description': f'Subject for {subject_name.strip()}'}
            )

        # Create quiz
        quiz = Quiz.objects.create(
            title=f"Quiz: {topic}",
            description=f"AI-generated quiz about {topic}",
            user=request.user,
            subject=subject,
            difficulty=difficulty,
            total_questions=len(questions_data)
        )

        # Create questions and choices
        for q_data in questions_data:
            question = Question.objects.create(
                quiz=quiz,
                question_text=q_data['question_text'],
                explanation=q_data.get('explanation', '')
            )

            for choice_data in q_data['choices']:
                Choice.objects.create(
                    question=question,
                    choice_text=choice_data['text'],
                    is_correct=choice_data['is_correct']
                )

        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
