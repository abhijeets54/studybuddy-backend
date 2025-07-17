"""
Analytics utility functions for tracking user activities and updating statistics
"""
from django.utils import timezone
from django.db.models import Avg
from datetime import date, timedelta
from .models import DailyActivity, StudyStreak, SubjectPerformance


def update_daily_activity(user, activity_type, **kwargs):
    """
    Update or create daily activity record for a user
    
    Args:
        user: User instance
        activity_type: 'quiz', 'flashcard', 'note'
        **kwargs: Additional data like score, study_time, etc.
    """
    today = timezone.now().date()
    
    # Get or create today's activity record
    activity, created = DailyActivity.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            'notes_created': 0,
            'quizzes_taken': 0,
            'flashcards_studied': 0,
            'study_time_minutes': 0,
            'quiz_score_average': 0.0
        }
    )
    
    # Update based on activity type
    if activity_type == 'quiz':
        activity.quizzes_taken += 1
        
        # Update quiz score average
        score = kwargs.get('score', 0)
        if activity.quizzes_taken == 1:
            activity.quiz_score_average = score
        else:
            # Calculate running average
            total_score = activity.quiz_score_average * (activity.quizzes_taken - 1) + score
            activity.quiz_score_average = total_score / activity.quizzes_taken
            
        # Add study time if provided
        study_time = kwargs.get('study_time_minutes', 0)
        activity.study_time_minutes += study_time
        
    elif activity_type == 'flashcard':
        cards_studied = kwargs.get('cards_studied', 1)
        activity.flashcards_studied += cards_studied
        
        study_time = kwargs.get('study_time_minutes', 0)
        activity.study_time_minutes += study_time
        
    elif activity_type == 'note':
        activity.notes_created += 1
    
    activity.save()
    
    # Update study streak
    update_study_streak(user)
    
    return activity


def update_study_streak(user):
    """
    Update user's study streak based on daily activities
    """
    # Get or create study streak record
    streak, created = StudyStreak.objects.get_or_create(
        user=user,
        defaults={
            'current_streak': 0,
            'longest_streak': 0,
            'last_study_date': None,
            'total_study_days': 0
        }
    )
    
    today = timezone.now().date()
    
    # Check if user has any activity today
    has_activity_today = DailyActivity.objects.filter(
        user=user,
        date=today
    ).exists()
    
    if has_activity_today:
        if streak.last_study_date is None:
            # First time studying
            streak.current_streak = 1
            streak.longest_streak = 1
            streak.total_study_days = 1
            streak.last_study_date = today
            
        elif streak.last_study_date == today:
            # Already studied today, no change needed
            pass
            
        elif streak.last_study_date == today - timedelta(days=1):
            # Consecutive day
            streak.current_streak += 1
            streak.total_study_days += 1
            streak.last_study_date = today
            
            # Update longest streak if needed
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
                
        else:
            # Streak broken, start new streak
            streak.current_streak = 1
            streak.total_study_days += 1
            streak.last_study_date = today
    
    streak.save()
    return streak


def update_subject_performance(user, quiz_attempt):
    """
    Update subject performance based on quiz attempt
    """
    quiz = quiz_attempt.quiz
    if not hasattr(quiz, 'subject') or not quiz.subject:
        return None
    
    # Get or create subject performance record
    performance, created = SubjectPerformance.objects.get_or_create(
        user=user,
        subject=quiz.subject,
        defaults={
            'total_quizzes': 0,
            'average_score': 0.0,
            'best_score': 0.0,
            'total_study_time': 0,
            'mastery_level': 0.0,
            'last_studied': timezone.now()
        }
    )
    
    # Update performance metrics
    performance.total_quizzes += 1
    performance.last_studied = timezone.now()
    
    # Update best score
    if quiz_attempt.score > performance.best_score:
        performance.best_score = quiz_attempt.score
    
    # Calculate new average score
    if performance.total_quizzes == 1:
        performance.average_score = quiz_attempt.score
    else:
        total_score = performance.average_score * (performance.total_quizzes - 1) + quiz_attempt.score
        performance.average_score = total_score / performance.total_quizzes
    
    # Add study time (convert quiz time from seconds to minutes)
    performance.total_study_time += quiz_attempt.time_taken // 60
    
    # Calculate mastery level (simple formula based on average score and consistency)
    performance.mastery_level = min(performance.average_score, 100.0)
    
    performance.save()
    return performance


def track_quiz_completion(user, quiz_attempt):
    """
    Track quiz completion and update all relevant analytics
    """
    # Calculate study time in minutes (quiz time_taken is in seconds)
    study_time_minutes = quiz_attempt.time_taken // 60
    
    # Update daily activity
    update_daily_activity(
        user=user,
        activity_type='quiz',
        score=quiz_attempt.score,
        study_time_minutes=study_time_minutes
    )
    
    # Update subject performance if quiz has a subject
    update_subject_performance(user, quiz_attempt)


def track_flashcard_session(user, flashcard_set, cards_studied, session_duration_seconds):
    """
    Track flashcard study session and update analytics
    """
    # Convert session duration to minutes
    study_time_minutes = session_duration_seconds // 60
    
    # Update daily activity
    update_daily_activity(
        user=user,
        activity_type='flashcard',
        cards_studied=cards_studied,
        study_time_minutes=study_time_minutes
    )


def get_user_analytics_summary(user):
    """
    Get a summary of user's analytics for debugging
    """
    # Get recent daily activities
    recent_activities = DailyActivity.objects.filter(user=user).order_by('-date')[:7]
    
    # Get study streak
    study_streak = StudyStreak.objects.filter(user=user).first()
    
    # Get subject performances
    subject_performances = SubjectPerformance.objects.filter(user=user)
    
    return {
        'recent_activities': list(recent_activities.values()),
        'study_streak': {
            'current_streak': study_streak.current_streak if study_streak else 0,
            'longest_streak': study_streak.longest_streak if study_streak else 0,
            'total_study_days': study_streak.total_study_days if study_streak else 0,
        },
        'subject_performances': list(subject_performances.values()),
        'total_daily_activities': DailyActivity.objects.filter(user=user).count(),
    }
