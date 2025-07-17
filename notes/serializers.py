from rest_framework import serializers
from .models import Note, Subject, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'created_at']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description', 'color', 'created_at']


class NoteSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    subject = SubjectSerializer(read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    subject_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Note
        fields = [
            'id', 'title', 'content', 'subject', 'subject_name', 'tags', 'tag_names',
            'difficulty', 'is_favorite', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        subject_name = validated_data.pop('subject_name', None)

        # Set the user from the request context
        validated_data['user'] = self.context['request'].user

        # Get or create subject if provided
        if subject_name and subject_name.strip():
            subject, created = Subject.objects.get_or_create(
                name=subject_name.strip(),
                defaults={'description': f'Subject for {subject_name.strip()}'}
            )
            validated_data['subject'] = subject

        note = Note.objects.create(**validated_data)

        # Handle tags
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(name=tag_name.strip())
            note.tags.add(tag)

        return note

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        subject_name = validated_data.pop('subject_name', None)

        # Update subject if provided
        if subject_name is not None:
            if subject_name and subject_name.strip():
                subject, created = Subject.objects.get_or_create(
                    name=subject_name.strip(),
                    defaults={'description': f'Subject for {subject_name.strip()}'}
                )
                instance.subject = subject
            else:
                instance.subject = None

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Handle tags if provided
        if tag_names is not None:
            instance.tags.clear()
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(name=tag_name.strip())
                instance.tags.add(tag)

        return instance


class NoteListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing notes"""
    tags = TagSerializer(many=True, read_only=True)
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Note
        fields = [
            'id', 'title', 'content', 'subject', 'tags', 'difficulty',
            'is_favorite', 'created_at', 'updated_at'
        ]
