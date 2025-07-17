from rest_framework import serializers
from .models import FlashcardSet, Flashcard, FlashcardProgress, StudySession
from notes.serializers import SubjectSerializer


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ['id', 'front_text', 'back_text', 'hint', 'order', 'created_at']


class FlashcardProgressSerializer(serializers.ModelSerializer):
    flashcard = FlashcardSerializer(read_only=True)
    
    class Meta:
        model = FlashcardProgress
        fields = [
            'id', 'flashcard', 'difficulty', 'review_count', 
            'last_reviewed', 'next_review', 'is_mastered'
        ]


class FlashcardSetSerializer(serializers.ModelSerializer):
    flashcards = FlashcardSerializer(many=True, read_only=True)
    subject = SubjectSerializer(read_only=True)
    
    class Meta:
        model = FlashcardSet
        fields = [
            'id', 'title', 'description', 'subject', 'is_public', 
            'created_at', 'updated_at', 'flashcards'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FlashcardSetListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing flashcard sets"""
    subject = SubjectSerializer(read_only=True)
    flashcard_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FlashcardSet
        fields = [
            'id', 'title', 'description', 'subject', 'is_public', 
            'created_at', 'updated_at', 'flashcard_count'
        ]
    
    def get_flashcard_count(self, obj):
        return obj.flashcards.count()


class FlashcardSetCreateSerializer(serializers.ModelSerializer):
    note_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    subject_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    subject_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = FlashcardSet
        fields = ['title', 'description', 'note_id', 'subject_id', 'subject_name', 'is_public']

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

        return FlashcardSet.objects.create(**validated_data)


class FlashcardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ['front_text', 'back_text', 'hint', 'order']


class StudySessionSerializer(serializers.ModelSerializer):
    flashcard_set = FlashcardSetListSerializer(read_only=True)
    
    class Meta:
        model = StudySession
        fields = [
            'id', 'flashcard_set', 'cards_studied', 'cards_mastered', 
            'session_duration', 'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'started_at']


class FlashcardReviewSerializer(serializers.Serializer):
    flashcard_id = serializers.IntegerField()
    difficulty = serializers.ChoiceField(choices=FlashcardProgress.DIFFICULTY_CHOICES)
    
    def validate_flashcard_id(self, value):
        try:
            flashcard = Flashcard.objects.get(id=value)
            # Check if user has access to this flashcard
            user = self.context['request'].user
            if flashcard.flashcard_set.user != user and not flashcard.flashcard_set.is_public:
                raise serializers.ValidationError("You don't have access to this flashcard")
            return value
        except Flashcard.DoesNotExist:
            raise serializers.ValidationError("Flashcard not found")
