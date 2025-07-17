import google.generativeai as genai
import json
import logging
from django.conf import settings
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiAIService:
    def __init__(self):
        # List of models in order of preference (best to fallback)
        self.model_names = [
            'gemini-2.5-flash',      # Best model
            'gemini-2.0-flash-exp',  # Experimental fallback
            'gemini-2.0-flash',      # Stable fallback
            'gemini-1.5-flash',      # Older but reliable
            'gemini-pro'             # Final fallback
        ]
        self.current_model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize with the best available model"""
        for model_name in self.model_names:
            try:
                self.current_model = genai.GenerativeModel(model_name)
                logger.info(f"Successfully initialized Gemini AI with model: {model_name}")
                break
            except Exception as e:
                logger.warning(f"Failed to initialize model {model_name}: {e}")
                continue

        if not self.current_model:
            raise Exception("Failed to initialize any Gemini model")

    def _generate_with_fallback(self, prompt: str, max_retries: int = 3):
        """Generate content with model fallback on failure"""
        # Generation configuration for better results
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,  # Balanced creativity and consistency
            top_p=0.8,       # Focus on most likely tokens
            top_k=40,        # Limit vocabulary for more focused responses
            max_output_tokens=4096,  # Allow for longer responses
            candidate_count=1
        )

        for attempt in range(max_retries):
            for model_name in self.model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(
                        prompt,
                        generation_config=generation_config
                    )

                    if response.text:
                        if model_name != self.model_names[0]:
                            logger.info(f"Successfully used fallback model: {model_name}")
                        return response
                    else:
                        logger.warning(f"Empty response from model: {model_name}")

                except Exception as e:
                    logger.warning(f"Model {model_name} failed (attempt {attempt + 1}): {e}")
                    continue

            if attempt < max_retries - 1:
                logger.info(f"Retrying generation (attempt {attempt + 2}/{max_retries})")

        raise Exception("All models failed to generate content after multiple attempts")

    def test_models(self):
        """Test which models are available and working"""
        working_models = []
        test_prompt = "Generate a simple test response: Hello World"

        for model_name in self.model_names:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(test_prompt)
                if response.text:
                    working_models.append(model_name)
                    logger.info(f"✓ Model {model_name} is working")
                else:
                    logger.warning(f"✗ Model {model_name} returned empty response")
            except Exception as e:
                logger.warning(f"✗ Model {model_name} failed: {e}")

        return working_models

    def _clean_json_response(self, response_text: str) -> str:
        """Clean AI response to extract valid JSON"""
        logger.info(f"Raw AI response: {response_text[:500]}...")  # Log first 500 chars for debugging

        # Remove markdown code blocks if present
        if '```json' in response_text:
            # Extract content between ```json and ```
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            if end != -1:
                response_text = response_text[start:end]
        elif '```' in response_text:
            # Handle generic code blocks
            start = response_text.find('```') + 3
            end = response_text.rfind('```')
            if end != -1 and end > start:
                response_text = response_text[start:end]

        # Remove any leading/trailing whitespace
        response_text = response_text.strip()

        # Remove any text before the first { or [
        json_start = min(
            response_text.find('{') if '{' in response_text else len(response_text),
            response_text.find('[') if '[' in response_text else len(response_text)
        )
        if json_start < len(response_text):
            response_text = response_text[json_start:]

        # Remove any text after the last } or ]
        json_end = max(
            response_text.rfind('}') + 1 if '}' in response_text else 0,
            response_text.rfind(']') + 1 if ']' in response_text else 0
        )
        if json_end > 0:
            response_text = response_text[:json_end]

        logger.info(f"Cleaned JSON: {response_text[:500]}...")  # Log cleaned JSON for debugging
        return response_text
    
    def generate_quiz_questions(self, note_content: str, note_title: str,
                              num_questions: int = 5, difficulty: str = 'medium') -> List[Dict[str, Any]]:
        """
        Generate quiz questions from note content using Gemini AI with fallback models
        """
        try:
            prompt = self._create_quiz_prompt(note_content, note_title, num_questions, difficulty)
            response = self._generate_with_fallback(prompt)

            if not response.text:
                raise Exception("Empty response from Gemini API")

            # Clean and parse the JSON response
            cleaned_response = self._clean_json_response(response.text)
            questions_data = json.loads(cleaned_response)
            
            # Validate the response structure
            if not isinstance(questions_data, dict) or 'questions' not in questions_data:
                raise Exception("Invalid response format from Gemini API")
            
            return questions_data['questions']
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {response.text}")
            raise Exception("Failed to parse AI response")
        except Exception as e:
            logger.error(f"Error generating quiz questions: {e}")
            raise Exception(f"Failed to generate quiz questions: {str(e)}")

    def generate_quiz_from_topic(self, topic: str, num_questions: int = 5, difficulty: str = 'medium') -> List[Dict[str, Any]]:
        """
        Generate quiz questions from just a topic using Gemini AI
        """
        try:
            # Use empty content to trigger topic-only generation
            prompt = self._create_quiz_prompt("", topic, num_questions, difficulty)
            response = self._generate_with_fallback(prompt)

            if not response.text:
                raise Exception("Empty response from Gemini API")

            # Clean and parse the JSON response
            cleaned_response = self._clean_json_response(response.text)
            questions_data = json.loads(cleaned_response)

            # Validate the response structure
            if not isinstance(questions_data, dict) or 'questions' not in questions_data:
                raise Exception("Invalid response format from Gemini API")

            return questions_data['questions']

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw response text: {response.text}")
            logger.error(f"Cleaned response text: {cleaned_response}")
            raise Exception(f"Failed to parse AI response: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating quiz from topic: {e}")
            raise Exception(f"Failed to generate quiz from topic: {str(e)}")

    def generate_flashcards(self, note_content: str, note_title: str,
                          num_cards: int = 10) -> List[Dict[str, str]]:
        """
        Generate flashcards from note content using Gemini AI with fallback models
        """
        try:
            prompt = self._create_flashcard_prompt(note_content, note_title, num_cards)
            response = self._generate_with_fallback(prompt)

            if not response.text:
                raise Exception("Empty response from Gemini API")

            # Clean and parse the JSON response
            cleaned_response = self._clean_json_response(response.text)
            flashcards_data = json.loads(cleaned_response)
            
            # Validate the response structure
            if not isinstance(flashcards_data, dict) or 'flashcards' not in flashcards_data:
                raise Exception("Invalid response format from Gemini API")
            
            return flashcards_data['flashcards']
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {response.text}")
            raise Exception("Failed to parse AI response")
        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            raise Exception(f"Failed to generate flashcards: {str(e)}")

    def generate_notes(self, topic: str, description: str = "", guidelines: str = "") -> str:
        """
        Generate comprehensive notes from a topic using Gemini AI
        """
        try:
            prompt = self._create_notes_prompt(topic, description, guidelines)
            response = self._generate_with_fallback(prompt)

            if not response.text:
                raise Exception("Empty response from Gemini API")

            return response.text.strip()

        except Exception as e:
            logger.error(f"Error generating notes: {e}")
            raise Exception(f"Failed to generate notes: {str(e)}")

    def _create_quiz_prompt(self, content: str, title: str, num_questions: int, difficulty: str) -> str:
        """Create a structured prompt for quiz generation"""
        difficulty_instructions = {
            'easy': 'Focus on basic concepts and definitions. Questions should test recall and understanding.',
            'medium': 'Include application and analysis questions. Mix recall with problem-solving.',
            'hard': 'Focus on synthesis, evaluation, and complex problem-solving. Include scenario-based questions.'
        }

        # Handle topic-only generation (when content is empty or minimal)
        if not content or len(content.strip()) < 10:
            prompt = f"""
You are an expert educational content creator specializing in quiz generation. Your task is to create high-quality multiple-choice questions about the given topic.

**TOPIC:** {title}

**GENERATION REQUIREMENTS:**
- Generate exactly {num_questions} multiple-choice questions about {title}
- Difficulty level: {difficulty}
- {difficulty_instructions.get(difficulty, difficulty_instructions['medium'])}
- Use your knowledge to create comprehensive questions about this topic
- Cover different aspects and subtopics related to {title}

**QUESTION STANDARDS:**
- Each question must have exactly 4 answer choices
- Only one choice should be correct
- Questions should cover important concepts related to {title}
- Use clear, academic language appropriate for the difficulty level
- Include educational explanations for correct answers
- Ensure questions test understanding, not just memorization
- Avoid ambiguous or trick questions

**Required JSON Format:**
{{
    "questions": [
        {{
            "question_text": "Your question here?",
            "choices": [
                {{"text": "Option A", "is_correct": false}},
                {{"text": "Option B", "is_correct": true}},
                {{"text": "Option C", "is_correct": false}},
                {{"text": "Option D", "is_correct": false}}
            ],
            "explanation": "Brief explanation of why the correct answer is right."
        }}
    ]
}}

Generate the quiz questions now:
"""
        else:
            prompt = f"""
You are an expert educational content creator specializing in quiz generation. Your task is to create high-quality multiple-choice questions based on the provided study material.

**CONTENT TO ANALYZE:**
Title: {title}
Content: {content}

**GENERATION REQUIREMENTS:**
- Generate exactly {num_questions} multiple-choice questions
- Difficulty level: {difficulty}
- {difficulty_instructions.get(difficulty, difficulty_instructions['medium'])}

**QUESTION STANDARDS:**
- Each question must have exactly 4 answer choices
- Only one choice should be correct
- Questions should directly relate to the provided content
- Use clear, academic language appropriate for the difficulty level
- Include educational explanations for correct answers
- Ensure questions test understanding, not just memorization
- Avoid ambiguous or trick questions

**Required JSON Format:**
{{
    "questions": [
        {{
            "question_text": "Your question here?",
            "choices": [
                {{"text": "Option A", "is_correct": false}},
                {{"text": "Option B", "is_correct": true}},
                {{"text": "Option C", "is_correct": false}},
                {{"text": "Option D", "is_correct": false}}
            ],
            "explanation": "Brief explanation of why the correct answer is right."
        }}
    ]
}}

Generate the quiz questions now:
"""
        return prompt
    
    def _create_flashcard_prompt(self, content: str, title: str, num_cards: int) -> str:
        """Create a structured prompt for flashcard generation"""
        prompt = f"""
You are an expert educational content creator specializing in flashcard generation for effective learning and retention.

**CONTENT TO ANALYZE:**
Title: {title}
Content: {content}

**GENERATION REQUIREMENTS:**
- Generate exactly {num_cards} high-quality flashcards
- Each flashcard must have a clear front (question/prompt) and back (answer)

**FLASHCARD STANDARDS:**
- Front: Concise, specific questions or prompts that test key concepts
- Back: Comprehensive yet concise answers with clear explanations
- Focus on essential information: definitions, concepts, formulas, processes
- Create a variety of card types: definitions, explanations, applications, examples
- Ensure questions are specific and have definitive answers
- Avoid yes/no questions or overly broad prompts
- Include helpful hints when appropriate to aid learning
- Use active recall principles to enhance memory retention

**Required JSON Format:**
{{
    "flashcards": [
        {{
            "front_text": "Question or prompt here",
            "back_text": "Answer or explanation here",
            "hint": "Optional hint (can be empty)"
        }}
    ]
}}

Generate the flashcards now:
"""
        return prompt

    def _create_notes_prompt(self, topic: str, description: str = "", guidelines: str = "") -> str:
        """Create a structured prompt for notes generation"""

        prompt = f"""
You are an expert educational content creator and teacher. Your task is to create comprehensive, well-structured study notes on the given topic.

**TOPIC:** {topic}
"""

        if description:
            prompt += f"""
**ADDITIONAL CONTEXT/DESCRIPTION:** {description}
"""

        if guidelines:
            prompt += f"""
**SPECIFIC GUIDELINES TO FOLLOW:** {guidelines}
"""

        prompt += f"""

**CONTENT REQUIREMENTS:**
- Create comprehensive, educational notes covering all important aspects of {topic}
- Structure the content with clear headings and subheadings
- Include key concepts, definitions, and explanations
- Use bullet points and numbered lists for clarity
- Add examples where appropriate to illustrate concepts
- Ensure the content is accurate and educationally sound
- Make the notes suitable for studying and review

**FORMATTING GUIDELINES:**
- Use markdown formatting for better readability
- Include clear section headers (##, ###)
- Use bullet points (-) and numbered lists (1., 2., 3.)
- Bold important terms and concepts
- Keep paragraphs concise and focused
- Ensure logical flow from basic to advanced concepts

**CONTENT STRUCTURE:**
1. Introduction/Overview
2. Key Concepts and Definitions
3. Main Topics (broken down into subsections)
4. Important Details and Examples
5. Summary/Key Takeaways

Generate comprehensive study notes now:
"""
        return prompt

# Global instance
ai_service = GeminiAIService()
