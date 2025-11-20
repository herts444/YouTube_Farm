"""
TTS Generator Module
Generates audio using Edge TTS
"""
import os
import asyncio
from typing import List, Optional
import edge_tts
import aiofiles


class TTSGenerator:
    """Generates audio using Edge TTS"""

    VOICES = {
        'russian': {
            'male': 'ru-RU-DmitryNeural',
            'female': 'ru-RU-SvetlanaNeural'
        },
        'english': {
            'male': 'en-US-GuyNeural',
            'female': 'en-US-JennyNeural'
        },
        'ukrainian': {
            'male': 'uk-UA-OstapNeural',
            'female': 'uk-UA-PolinaNeural'
        }
    }

    def __init__(self):
        """Initialize TTS Generator"""
        pass

    async def generate_audio(
        self,
        text: str,
        output_path: str,
        language: str = 'russian',
        voice_gender: str = 'male',
        rate: str = '+0%',
        pitch: str = '+0Hz'
    ) -> str:
        """
        Generate audio from text

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            language: Language code
            voice_gender: Voice gender ('male' or 'female')
            rate: Speech rate (e.g., '+10%', '-5%')
            pitch: Speech pitch (e.g., '+5Hz', '-2Hz')

        Returns:
            Path to generated audio file
        """
        voice = self.VOICES.get(language, {}).get(voice_gender, 'ru-RU-DmitryNeural')

        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(output_path)

        return output_path

    async def generate_multiple_audio_async(
        self,
        texts: List[str],
        output_dir: str,
        language: str = 'russian',
        voice_gender: str = 'male'
    ) -> List[str]:
        """Generate multiple audio files asynchronously"""
        os.makedirs(output_dir, exist_ok=True)

        tasks = []
        output_paths = []

        for i, text in enumerate(texts):
            output_path = os.path.join(output_dir, f"scene_{i+1:03d}.mp3")
            output_paths.append(output_path)
            tasks.append(
                self.generate_audio(text, output_path, language, voice_gender)
            )

        await asyncio.gather(*tasks)

        return output_paths

    def get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds"""
        import subprocess
        from utils.config import FFPROBE_BIN

        cmd = [
            FFPROBE_BIN,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
