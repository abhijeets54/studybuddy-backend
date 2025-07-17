from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .models import StudyStreak, DailyActivity, SubjectPerformance, WeeklyGoal, Achievement
from .serializers import (
    StudyStreakSerializer, DailyActivitySerializer, SubjectPerformanceSerializer,
    WeeklyGoalSerializer, AchievementSerializer
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get comprehensive dashboard statistics"""
    user = request.user

    # Get or create study streak
    study_streak, created = StudyStreak.objects.get_or_create(user=user)

    # Get recent activity (last 30 days)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    recent_activities = DailyActivity.objects.filter(
        user=user,
        date__gte=thirty_days_ago
    ).order_by('-date')

    # Get subject performances
    subject_performances = SubjectPerformance.objects.filter(user=user).order_by('-average_score')

    # Get current week goals
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    current_goals = WeeklyGoal.objects.filter(
        user=user,
        week_start=week_start
    )

    # Get recent achievements
    recent_achievements = Achievement.objects.filter(user=user).order_by('-earned_at')[:5]

    # Calculate overall stats
    total_notes = user.notes.count()
    total_quizzes = user.quiz_attempts.count()
    total_flashcard_decks = user.flashcard_sets.count()
    avg_quiz_score = user.quiz_attempts.aggregate(avg_score=Avg('score'))['avg_score'] or 0

    stats = {
        'study_streak': StudyStreakSerializer(study_streak).data,
        'total_notes': total_notes,
        'total_quizzes': total_quizzes,
        'total_flashcard_decks': total_flashcard_decks,
        'average_quiz_score': round(avg_quiz_score, 2),
        'recent_activities': DailyActivitySerializer(recent_activities[:7], many=True).data,
        'subject_performances': SubjectPerformanceSerializer(subject_performances, many=True).data,
        'current_goals': WeeklyGoalSerializer(current_goals, many=True).data,
        'recent_achievements': AchievementSerializer(recent_achievements, many=True).data,
        'weekly_activity': []
    }

    # Get weekly activity for chart
    for i in range(7):
        date = today - timedelta(days=i)
        try:
            activity = DailyActivity.objects.get(user=user, date=date)
            stats['weekly_activity'].append({
                'date': date,
                'total_activity': (
                    activity.notes_created +
                    activity.quizzes_taken +
                    activity.flashcards_studied
                )
            })
        except DailyActivity.DoesNotExist:
            stats['weekly_activity'].append({
                'date': date,
                'total_activity': 0
            })

    stats['weekly_activity'].reverse()  # Show oldest to newest

    return Response(stats)


