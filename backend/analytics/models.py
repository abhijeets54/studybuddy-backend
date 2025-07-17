from django.db import models
from django.contrib.auth.models import User
from notes.models import Subject


class StudyStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='study_streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)
    total_study_days = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.current_streak} days"


class DailyActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_activities')
    date = models.DateField()
    notes_created = models.IntegerField(default=0)
    quizzes_taken = models.IntegerField(default=0)
    flashcards_studied = models.IntegerField(default=0)
    study_time_minutes = models.IntegerField(default=0)
    quiz_score_average = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']


class SubjectPerformance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subject_performances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='performances')
    total_quizzes = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    best_score = models.FloatField(default=0.0)
    total_study_time = models.IntegerField(default=0)  # in minutes
    mastery_level = models.FloatField(default=0.0)  # 0-100%
    last_studied = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.subject.name}"

    class Meta:
        unique_together = ['user', 'subject']
        ordering = ['-average_score']


class WeeklyGoal(models.Model):
    GOAL_TYPES = [
        ('quizzes', 'Quizzes Taken'),
        ('notes', 'Notes Created'),
        ('flashcards', 'Flashcards Studied'),
        ('study_time', 'Study Time (minutes)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    target_value = models.IntegerField()
    current_value = models.IntegerField(default=0)
    week_start = models.DateField()
    week_end = models.DateField()
    is_achieved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.goal_type} - Week {self.week_start}"

    class Meta:
        unique_together = ['user', 'goal_type', 'week_start']
        ordering = ['-week_start']


class Achievement(models.Model):
    ACHIEVEMENT_TYPES = [
        ('first_quiz', 'First Quiz Completed'),
        ('quiz_streak_5', '5 Quiz Streak'),
        ('quiz_streak_10', '10 Quiz Streak'),
        ('perfect_score', 'Perfect Quiz Score'),
        ('study_streak_7', '7 Day Study Streak'),
        ('study_streak_30', '30 Day Study Streak'),
        ('notes_milestone_10', '10 Notes Created'),
        ('notes_milestone_50', '50 Notes Created'),
        ('flashcard_master', '100 Flashcards Mastered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=30, choices=ACHIEVEMENT_TYPES)
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='🏆')
    earned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    class Meta:
        unique_together = ['user', 'achievement_type']
        ordering = ['-earned_at']
