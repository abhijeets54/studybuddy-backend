# Generated by Django 5.0.1 on 2025-07-15 12:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('notes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FlashcardSet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('note', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='flashcard_sets', to='notes.note')),
                ('subject', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='notes.subject')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flashcard_sets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Flashcard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('front_text', models.TextField()),
                ('back_text', models.TextField()),
                ('hint', models.TextField(blank=True)),
                ('order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('flashcard_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flashcards', to='flashcards.flashcardset')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='StudySession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cards_studied', models.IntegerField(default=0)),
                ('cards_mastered', models.IntegerField(default=0)),
                ('session_duration', models.IntegerField(default=0)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('flashcard_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='study_sessions', to='flashcards.flashcardset')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='study_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='FlashcardProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('difficulty', models.CharField(choices=[('again', 'Again'), ('hard', 'Hard'), ('good', 'Good'), ('easy', 'Easy')], default='good', max_length=10)),
                ('review_count', models.IntegerField(default=0)),
                ('last_reviewed', models.DateTimeField(auto_now=True)),
                ('next_review', models.DateTimeField(blank=True, null=True)),
                ('is_mastered', models.BooleanField(default=False)),
                ('flashcard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress', to='flashcards.flashcard')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flashcard_progress', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-last_reviewed'],
                'unique_together': {('user', 'flashcard')},
            },
        ),
    ]
