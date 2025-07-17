from rest_framework import serializers
from .models import StudyStreak, DailyActivity, SubjectPerformance, WeeklyGoal, Achievement
from notes.serializers import SubjectSerializer


class StudyStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyStreak
        fields = [
            'current_streak', 'longest_streak', 'last_study_date', 'total_study_days'
        ]


class DailyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActivity
        fields = [
            'date', 'notes_created', 'quizzes_taken', 'flashcards_studied',
            'study_time_minutes', 'quiz_score_average'
        ]


class SubjectPerformanceSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    
    class Meta:
        model = SubjectPerformance
        fields = [
            'subject', 'total_quizzes', 'average_score', 'best_score',
            'total_study_time', 'mastery_level', 'last_studied'
        ]


class WeeklyGoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = WeeklyGoal
        fields = [
            'id', 'goal_type', 'target_value', 'current_value', 
            'week_start', 'week_end', 'is_achieved', 'progress_percentage'
        ]
    
    def get_progress_percentage(self, obj):
        if obj.target_value == 0:
            return 0
        return min(100, (obj.current_value / obj.target_value) * 100)



class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = [
            'id', 'achievement_type', 'title', 'description', 
            'icon', 'earned_at'
        ]
