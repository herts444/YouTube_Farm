"""
Video Assembler Module
Assembles final video from images and audio using MoviePy
"""
import os
from typing import List, Dict
from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    CompositeVideoClip, VideoClip
)
import numpy as np


class VideoAssembler:
    """Assembles video from images and audio"""

    def __init__(self, fps: int = 30, resolution: tuple = (1920, 1080)):
        """
        Initialize Video Assembler

        Args:
            fps: Frames per second
            resolution: Video resolution (width, height)
        """
        self.fps = fps
        self.resolution = resolution

    def create_video_with_scene_audio(
        self,
        scenes: List[Dict],
        output_path: str,
        fade_duration: float = 0.5,
        zoom_effect: bool = True,
        zoom_factor: float = 1.1
    ) -> str:
        """
        Create video with synchronized audio for each scene

        Args:
            scenes: List of scene dicts with 'image_path' and 'audio_path'
            output_path: Path to save the video
            fade_duration: Duration of fade transitions
            zoom_effect: Apply Ken Burns zoom effect
            zoom_factor: Zoom factor for Ken Burns effect

        Returns:
            Path to generated video
        """
        video_clips = []

        for i, scene in enumerate(scenes):
            # Load audio to get duration
            audio = AudioFileClip(scene['audio_path'])
            duration = audio.duration

            # Create image clip
            img_clip = ImageClip(scene['image_path'], duration=duration)
            img_clip = img_clip.set_fps(self.fps)

            # Resize to target resolution
            img_clip = img_clip.resize(self.resolution)

            # Apply Ken Burns zoom effect
            if zoom_effect:
                img_clip = self._apply_ken_burns(img_clip, zoom_factor)

            # Set audio
            img_clip = img_clip.set_audio(audio)

            # Add fade in/out
            if i == 0:
                # First scene: fade in only
                img_clip = img_clip.fadein(fade_duration)
            elif i == len(scenes) - 1:
                # Last scene: fade out only
                img_clip = img_clip.fadeout(fade_duration)
            else:
                # Middle scenes: crossfade handled by concatenate
                pass

            video_clips.append(img_clip)

        # Concatenate all clips with crossfade
        final_video = concatenate_videoclips(
            video_clips,
            method="compose",
            padding=-fade_duration if len(video_clips) > 1 else 0
        )

        # Write video
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            bitrate='5000k',
            threads=4
        )

        # Clean up
        final_video.close()
        for clip in video_clips:
            clip.close()

        return output_path

    def _apply_ken_burns(self, clip: ImageClip, zoom_factor: float = 1.1) -> VideoClip:
        """
        Apply Ken Burns zoom effect to image clip

        Args:
            clip: Image clip
            zoom_factor: Zoom factor (1.0 = no zoom, 1.1 = 10% zoom)

        Returns:
            Video clip with zoom effect
        """
        def zoom_in(t):
            # Progress from 0 to 1 over the duration
            progress = t / clip.duration
            # Scale from 1.0 to zoom_factor
            scale = 1.0 + (zoom_factor - 1.0) * progress
            return scale

        def make_frame(t):
            frame = clip.get_frame(t)
            scale = zoom_in(t)

            h, w = frame.shape[:2]
            new_h = int(h * scale)
            new_w = int(w * scale)

            # Resize frame
            from PIL import Image
            img = Image.fromarray(frame)
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)

            # Crop to original size (centered)
            crop_x = (new_w - w) // 2
            crop_y = (new_h - h) // 2
            img_cropped = img_resized.crop((crop_x, crop_y, crop_x + w, crop_y + h))

            return np.array(img_cropped)

        return VideoClip(make_frame, duration=clip.duration)
