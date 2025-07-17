from django.db import models
from django.contrib.auth.models import User
from notes.models import Note, Subject


class FlashcardSet(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flashcard_sets')
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='flashcard_sets', null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-updated_at']


class Flashcard(models.Model):
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE, related_name='flashcards')
    front_text = models.TextField()
    back_text = models.TextField()
    hint = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.flashcard_set.title} - Card {self.order}"

    class Meta:
        ordering = ['order']


class FlashcardProgress(models.Model):
    DIFFICULTY_CHOICES = [
        ('again', 'Again'),
        ('hard', 'Hard'),
        ('good', 'Good'),
        ('easy', 'Easy'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flashcard_progress')
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name='progress')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='good')
    review_count = models.IntegerField(default=0)
    last_reviewed = models.DateTimeField(auto_now=True)
    next_review = models.DateTimeField(null=True, blank=True)
    is_mastered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.flashcard}"

    class Meta:
        unique_together = ['user', 'flashcard']
        ordering = ['-last_reviewed']


class StudySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE, related_name='study_sessions')
    cards_studied = models.IntegerField(default=0)
    cards_mastered = models.IntegerField(default=0)
    session_duration = models.IntegerField(default=0)  # in seconds
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.flashcard_set.title} - {self.started_at.date()}"

    class Meta:
        ordering = ['-started_at']
