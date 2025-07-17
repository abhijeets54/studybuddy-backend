from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAttempt, UserAnswer
from notes.serializers import SubjectSerializer


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'choice_text', 'is_correct', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'explanation', 'order', 'choices']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    subject = SubjectSerializer(read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'subject', 'difficulty', 
            'time_limit', 'total_questions', 'created_at', 'questions'
        ]
        read_only_fields = ['id', 'created_at']


class QuizListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing quizzes"""
    subject = SubjectSerializer(read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'subject', 'difficulty', 
            'time_limit', 'total_questions', 'created_at'
        ]


class QuizCreateSerializer(serializers.ModelSerializer):
    note_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    subject_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    subject_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'note_id', 'subject_id', 'subject_name',
            'difficulty', 'time_limit', 'total_questions'
        ]

    def create(self, validated_data):
        note_id = validated_data.pop('note_id', None)
        subject_id = validated_data.pop('subject_id', None)
        subject_name = validated_data.pop('subject_name', None)

        # Set the user from the request context
        validated_data['user'] = self.context['request'].user

        # Set note and subject if provided
        if note_id:
            from notes.models import Note
            try:
                note = Note.objects.get(id=note_id, user=self.context['request'].user)
                validated_data['note'] = note
                if not subject_id and not subject_name and note.subject:
                    validated_data['subject'] = note.subject
            except Note.DoesNotExist:
                pass

        # Handle subject by ID (legacy)
        if subject_id:
            from notes.models import Subject
            try:
                subject = Subject.objects.get(id=subject_id)
                validated_data['subject'] = subject
            except Subject.DoesNotExist:
                pass
        # Handle subject by name (new approach)
        elif subject_name and subject_name.strip():
            from notes.models import Subject
            subject, created = Subject.objects.get_or_create(
                name=subject_name.strip(),
                defaults={'description': f'Subject for {subject_name.strip()}'}
            )
            validated_data['subject'] = subject

        return Quiz.objects.create(**validated_data)


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['question', 'selected_choice', 'is_correct']


class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = UserAnswerSerializer(many=True, read_only=True)
    quiz = QuizListSerializer(read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz', 'score', 'total_questions', 'correct_answers', 
            'time_taken', 'completed_at', 'answers'
        ]
        read_only_fields = ['id', 'completed_at']


class QuizSubmissionSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
    time_taken = serializers.IntegerField()

    def validate_answers(self, value):
        """Validate that answers have the correct format"""
        for answer in value:
            if 'question_id' not in answer or 'choice_id' not in answer:
                raise serializers.ValidationError(
                    "Each answer must have 'question_id' and 'choice_id'"
                )
        return value
