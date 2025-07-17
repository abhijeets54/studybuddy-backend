from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notes.models import Subject, Note, Tag


class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        # Create subjects
        subjects_data = [
            {'name': 'Mathematics', 'description': 'Math subjects including algebra, calculus, geometry', 'color': '#007bff'},
            {'name': 'Science', 'description': 'Physics, Chemistry, Biology', 'color': '#28a745'},
            {'name': 'History', 'description': 'World history and historical events', 'color': '#dc3545'},
            {'name': 'Literature', 'description': 'English literature and writing', 'color': '#6f42c1'},
            {'name': 'Computer Science', 'description': 'Programming and computer science concepts', 'color': '#fd7e14'},
        ]

        for subject_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                name=subject_data['name'],
                defaults=subject_data
            )
            if created:
                self.stdout.write(f'Created subject: {subject.name}')

        # Create tags
        tags_data = ['algebra', 'calculus', 'geometry', 'physics', 'chemistry', 'biology', 
                    'history', 'literature', 'programming', 'algorithms', 'data-structures']

        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            if created:
                self.stdout.write(f'Created tag: {tag.name}')

        # Get test user
        try:
            user = User.objects.get(username='testuser')
        except User.DoesNotExist:
            self.stdout.write('Test user not found. Please create a user first.')
            return

        # Create sample notes
        math_subject = Subject.objects.get(name='Mathematics')
        science_subject = Subject.objects.get(name='Science')
        cs_subject = Subject.objects.get(name='Computer Science')

        notes_data = [
            {
                'title': 'Introduction to Algebra',
                'content': '''Algebra is a branch of mathematics dealing with symbols and the rules for manipulating those symbols. 

Key concepts:
- Variables: Letters that represent unknown numbers (x, y, z)
- Equations: Mathematical statements that show equality (2x + 3 = 7)
- Functions: Relationships between inputs and outputs f(x) = 2x + 1

Basic operations:
1. Addition and subtraction of like terms
2. Multiplication and division of variables
3. Solving linear equations
4. Factoring polynomials

Example: Solve 2x + 5 = 13
Step 1: Subtract 5 from both sides: 2x = 8
Step 2: Divide by 2: x = 4''',
                'subject': math_subject,
                'difficulty': 'easy',
                'tags': ['algebra']
            },
            {
                'title': 'Newton\'s Laws of Motion',
                'content': '''Newton's three laws of motion are fundamental principles in physics.

First Law (Law of Inertia):
An object at rest stays at rest, and an object in motion stays in motion at constant velocity, unless acted upon by an external force.

Second Law (F = ma):
The acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass.
Formula: Force = mass × acceleration

Third Law (Action-Reaction):
For every action, there is an equal and opposite reaction.

Applications:
- Car safety (seatbelts, airbags)
- Rocket propulsion
- Walking and running
- Sports activities

Example: A 10 kg object experiences a 50 N force
Acceleration = Force / mass = 50 N / 10 kg = 5 m/s²''',
                'subject': science_subject,
                'difficulty': 'medium',
                'tags': ['physics']
            },
            {
                'title': 'Data Structures: Arrays and Lists',
                'content': '''Data structures are ways of organizing and storing data in a computer so that it can be accessed and modified efficiently.

Arrays:
- Fixed-size sequential collection of elements
- Elements are stored in contiguous memory locations
- Access time: O(1) for index-based access
- Insertion/deletion: O(n) in worst case

Lists (Dynamic Arrays):
- Variable-size collection of elements
- Can grow or shrink during runtime
- Common operations: append, insert, remove, search

Python List Example:
```python
# Creating a list
numbers = [1, 2, 3, 4, 5]

# Adding elements
numbers.append(6)  # [1, 2, 3, 4, 5, 6]
numbers.insert(0, 0)  # [0, 1, 2, 3, 4, 5, 6]

# Removing elements
numbers.remove(3)  # [0, 1, 2, 4, 5, 6]
numbers.pop()  # [0, 1, 2, 4, 5]
```

Time Complexities:
- Access: O(1)
- Search: O(n)
- Insertion: O(1) at end, O(n) at beginning
- Deletion: O(1) at end, O(n) at beginning''',
                'subject': cs_subject,
                'difficulty': 'medium',
                'tags': ['programming', 'data-structures']
            }
        ]

        for note_data in notes_data:
            tags = note_data.pop('tags', [])
            note, created = Note.objects.get_or_create(
                title=note_data['title'],
                user=user,
                defaults=note_data
            )
            if created:
                # Add tags
                for tag_name in tags:
                    tag = Tag.objects.get(name=tag_name)
                    note.tags.add(tag)
                self.stdout.write(f'Created note: {note.title}')

        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
