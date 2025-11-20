"""
Story Generator Module
Generates historical stories using OpenAI API
"""
import os
from typing import Dict, List, Optional
from openai import OpenAI
from utils.config import OPENAI_API_KEY


class StoryGenerator:
    """Generates historical stories and image prompts using OpenAI"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Story Generator"""
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key not found in config")

        self.client = OpenAI(api_key=self.api_key)

    def generate_historical_story(
        self,
        topic: str,
        language: str = 'russian',
        duration_seconds: int = 600,
        num_scenes: int = 30
    ) -> Dict:
        """
        Generate a historical story with scenes and image prompts

        Args:
            topic: Historical topic
            language: Language for the story ('russian', 'english', 'ukrainian')
            duration_seconds: Target duration of the video
            num_scenes: Number of scenes/images to generate

        Returns:
            Dict with story structure
        """
        language_names = {
            'russian': 'Russian',
            'ukrainian': 'Ukrainian',
            'english': 'English'
        }
        language_name = language_names.get(language, 'Russian')

        system_prompt = f"""You are a master storyteller specializing in creating CAPTIVATING, DRAMATIC historical narratives for video content.

Your mission: Create a {duration_seconds}-second historical story in {language_name} that will GRIP viewers from the first second.

Story Requirements:
✓ DRAMATIC OPENING: Start with a powerful hook that immediately captures attention
✓ EMOTIONAL DEPTH: Include human emotions, personal stories, dramatic moments
✓ VIVID DETAILS: Paint scenes with sensory details - sounds, sights, feelings
✓ NARRATIVE TENSION: Build suspense and drama throughout
✓ FACTUALLY ACCURATE: Based on real historical events
✓ CINEMATIC FLOW: Each scene flows naturally to the next
✓ EXACTLY {num_scenes} SCENES: Each scene represents one powerful moment

Storytelling Style:
- Use active voice and present tense for immediacy
- Include specific dates, names, and locations when relevant
- Create emotional connection with historical figures
- Show don't just tell - describe actions and scenes vividly
- End with powerful conclusion or lasting impact

Format your response as JSON with this structure:
{{
    "title": "Captivating story title",
    "full_text": "Complete dramatic narrative",
    "scenes": [
        {{
            "text": "Dramatic narrative for this scene with vivid details",
            "duration": 20.0,
            "image_prompt": "Highly detailed, cinematic image prompt in English"
        }}
    ]
}}

Image Prompts Requirements (CRITICAL):
- ALWAYS in ENGLISH (for AI image model)
- CINEMATIC and DRAMATIC composition
- Include:
  * Main subject and action
  * Setting and time of day
  * Mood and atmosphere
  * Lighting (dramatic lighting, golden hour, etc.)
  * Art style: "cinematic photography", "epic historical painting", "dramatic illustration"
  * Camera angle: "wide shot", "close-up", "aerial view"
- Example: "Napoleon Bonaparte on horseback watching Moscow burn at night, dramatic flames illuminating his face, epic historical painting style, wide cinematic shot, dark moody atmosphere"
- Focus on VISUAL IMPACT and DRAMA
"""

        user_prompt = f"Create a historical story about: {topic}"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )

            import json
            story_data = json.loads(response.choices[0].message.content)

            # Validate and normalize durations
            total_duration = sum(scene['duration'] for scene in story_data['scenes'])
            if abs(total_duration - duration_seconds) > 5:
                scale = duration_seconds / total_duration
                for scene in story_data['scenes']:
                    scene['duration'] *= scale

            return story_data

        except Exception as e:
            raise Exception(f"Error generating story: {str(e)}")

    def generate_topic_suggestions(
        self,
        num_suggestions: int = 5,
        language: str = 'russian'
    ) -> List[str]:
        """Generate interesting historical topic suggestions"""
        language_names = {
            'russian': 'Russian',
            'ukrainian': 'Ukrainian',
            'english': 'English'
        }
        language_name = language_names.get(language, 'Russian')

        prompt = f"""Generate {num_suggestions} CAPTIVATING historical event topics that will make viewers stop scrolling and watch.

Requirements for each topic:
✓ DRAMATIC and INTRIGUING: Must spark immediate curiosity
✓ SPECIFIC MOMENT: Focus on a specific event, not general periods
✓ EMOTIONALLY POWERFUL: Include human drama, tragedy, triumph, or mystery
✓ VISUALLY COMPELLING: Can be illustrated with dramatic imagery
✓ LESSER-KNOWN DETAILS: Include surprising or little-known historical moments
✓ DIVERSE TOPICS: Mix different time periods, cultures, and types of events
✓ In {language_name}

Format as JSON object:
{{
    "topics": ["Dramatic topic 1", "Dramatic topic 2", ...]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.9,
            )

            import json
            result = json.loads(response.choices[0].message.content)
            return result.get('topics', [])

        except Exception as e:
            raise Exception(f"Error generating topic suggestions: {str(e)}")
