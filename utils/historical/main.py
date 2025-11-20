"""
Main script for Historical Video Generation
Combines story generation, TTS, image generation, and video assembly
"""
import os
import json
from datetime import datetime
from typing import Optional, Dict

from .story_generator import StoryGenerator
from .tts_generator import TTSGenerator
from .image_generator import ImageGenerator
from .video_assembler import VideoAssembler


class HistoricalVideoGenerator:
    """Main class for generating complete historical videos"""

    def __init__(
        self,
        output_base_dir: str = "./out/historical_videos"
    ):
        """
        Initialize Historical Video Generator

        Args:
            output_base_dir: Base directory for output files
        """
        self.output_base_dir = output_base_dir
        os.makedirs(output_base_dir, exist_ok=True)

        # Initialize modules
        self.story_generator = StoryGenerator()
        self.tts_generator = TTSGenerator()
        self.image_generator = ImageGenerator()
        self.video_assembler = VideoAssembler(fps=30, resolution=(1920, 1080))

    async def generate_video(
        self,
        topic: str,
        language: str = 'russian',
        duration_seconds: int = 600,
        num_scenes: int = 30,
        voice_gender: str = 'male',
        output_name: Optional[str] = None,
        zoom_effect: bool = True,
        fade_duration: float = 0.5,
        num_inference_steps: int = 4,
        image_width: int = 1024,
        image_height: int = 576
    ) -> Dict:
        """
        Generate a complete historical video

        Args:
            topic: Historical topic
            language: Language ('russian', 'english', 'ukrainian')
            duration_seconds: Target video duration in seconds
            num_scenes: Number of scenes
            voice_gender: Voice gender ('male' or 'female')
            output_name: Custom output name (auto-generated if None)
            zoom_effect: Apply Ken Burns zoom effect
            fade_duration: Duration of fade transitions
            num_inference_steps: Inference steps for image generation
            image_width: Image width
            image_height: Image height

        Returns:
            Dictionary with paths to generated files
        """
        # Create timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_name:
            project_name = output_name
        else:
            project_name = f"{topic[:30]}_{timestamp}".replace(" ", "_")

        project_dir = os.path.join(self.output_base_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)

        images_dir = os.path.join(project_dir, "images")
        audio_dir = os.path.join(project_dir, "audio")
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

        # Step 1: Generate story
        story_data = self.story_generator.generate_historical_story(
            topic=topic,
            language=language,
            duration_seconds=duration_seconds,
            num_scenes=num_scenes
        )

        # Save story data
        story_path = os.path.join(project_dir, "story.json")
        with open(story_path, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        # Step 2: Generate audio for each scene
        scene_texts = [scene['text'] for scene in story_data['scenes']]

        audio_paths = await self.tts_generator.generate_multiple_audio_async(
            texts=scene_texts,
            output_dir=audio_dir,
            language=language,
            voice_gender=voice_gender
        )

        # Step 3: Generate images for each scene
        image_prompts = [scene['image_prompt'] for scene in story_data['scenes']]

        image_paths = await self.image_generator.generate_images(
            prompts=image_prompts,
            output_dir=images_dir,
            width=image_width,
            height=image_height,
            num_inference_steps=num_inference_steps,
            seed_start=42
        )

        # Step 4: Assemble video
        scenes = []
        for i in range(len(story_data['scenes'])):
            scenes.append({
                'image_path': image_paths[i],
                'audio_path': audio_paths[i]
            })

        # Generate video
        video_path = os.path.join(project_dir, f"{project_name}.mp4")

        final_video_path = self.video_assembler.create_video_with_scene_audio(
            scenes=scenes,
            output_path=video_path,
            fade_duration=fade_duration,
            zoom_effect=zoom_effect,
            zoom_factor=1.1
        )

        # Generate result summary
        result = {
            'video_path': final_video_path,
            'project_dir': project_dir,
            'story_path': story_path,
            'title': story_data['title'],
            'topic': topic,
            'language': language,
            'num_scenes': len(scenes),
            'image_paths': image_paths,
            'audio_paths': audio_paths,
            'timestamp': timestamp
        }

        # Save result metadata
        result_path = os.path.join(project_dir, "metadata.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    def generate_topic_suggestions(
        self,
        num_suggestions: int = 10,
        language: str = 'russian'
    ) -> list:
        """Get topic suggestions"""
        return self.story_generator.generate_topic_suggestions(
            num_suggestions=num_suggestions,
            language=language
        )
