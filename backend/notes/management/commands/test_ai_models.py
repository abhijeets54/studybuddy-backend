from django.core.management.base import BaseCommand
from studybuddy.ai_service import ai_service


class Command(BaseCommand):
    help = 'Test which Gemini AI models are available and working'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Gemini AI models...'))
        
        try:
            working_models = ai_service.test_models()
            
            if working_models:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ Found {len(working_models)} working models:')
                )
                for i, model in enumerate(working_models, 1):
                    status = "PRIMARY" if i == 1 else "FALLBACK"
                    self.stdout.write(f'  {i}. {model} ({status})')
                
                # Test actual generation
                self.stdout.write('\nTesting flashcard generation...')
                try:
                    flashcards = ai_service.generate_flashcards(
                        note_content="Photosynthesis is the process by which plants convert sunlight into energy.",
                        note_title="Photosynthesis Basics",
                        num_cards=2
                    )
                    self.stdout.write(self.style.SUCCESS('✓ Flashcard generation working'))
                    self.stdout.write(f'Generated {len(flashcards)} flashcards')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ Flashcard generation failed: {e}'))
                
                self.stdout.write('\nTesting quiz generation...')
                try:
                    questions = ai_service.generate_quiz_questions(
                        note_content="Photosynthesis is the process by which plants convert sunlight into energy.",
                        note_title="Photosynthesis Basics",
                        num_questions=2
                    )
                    self.stdout.write(self.style.SUCCESS('✓ Quiz generation working'))
                    self.stdout.write(f'Generated {len(questions)} questions')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ Quiz generation failed: {e}'))
                    
            else:
                self.stdout.write(
                    self.style.ERROR('✗ No working models found. Check your API key and internet connection.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing models: {e}')
            )
