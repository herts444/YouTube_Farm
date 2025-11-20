"""
Image Generator Module
Generates images using FAL.ai API
"""
import os
import asyncio
from typing import List, Optional
import aiohttp
import aiofiles
from utils.config import FAL_API_KEY


class ImageGenerator:
    """Generates images using FAL.ai FLUX model"""

    def __init__(self):
        """Initialize Image Generator"""
        self.api_key = FAL_API_KEY
        if not self.api_key or self.api_key == "your_fal_api_key_here":
            raise ValueError("FAL_API_KEY not set in .env file")

        self.base_url = "https://fal.run/fal-ai/flux/schnell"

    async def generate_image(
        self,
        prompt: str,
        output_path: str,
        width: int = 1024,
        height: int = 576,
        num_inference_steps: int = 4,
        seed: Optional[int] = None
    ) -> str:
        """
        Generate a single image

        Args:
            prompt: Image generation prompt
            output_path: Path to save the image
            width: Image width
            height: Image height
            num_inference_steps: Number of inference steps (4 recommended for schnell)
            seed: Random seed for reproducibility

        Returns:
            Path to generated image
        """
        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "image_size": {
                "width": width,
                "height": height
            },
            "num_inference_steps": num_inference_steps,
            "num_images": 1,
            "enable_safety_checker": False
        }

        if seed is not None:
            payload["seed"] = seed

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"FAL API error: {response.status} - {error_text}")

                result = await response.json()

                if 'images' in result and len(result['images']) > 0:
                    image_url = result['images'][0]['url']

                    # Download image
                    async with session.get(image_url) as img_response:
                        if img_response.status == 200:
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            async with aiofiles.open(output_path, 'wb') as f:
                                await f.write(await img_response.read())
                            return output_path
                        else:
                            raise Exception(f"Failed to download image: {img_response.status}")
                else:
                    raise Exception("No images generated")

    async def generate_images(
        self,
        prompts: List[str],
        output_dir: str,
        width: int = 1024,
        height: int = 576,
        num_inference_steps: int = 4,
        seed_start: int = 42
    ) -> List[str]:
        """Generate multiple images asynchronously"""
        os.makedirs(output_dir, exist_ok=True)

        tasks = []
        output_paths = []

        for i, prompt in enumerate(prompts):
            output_path = os.path.join(output_dir, f"scene_{i+1:03d}.png")
            output_paths.append(output_path)

            # Add delay between requests to avoid rate limiting
            if i > 0:
                await asyncio.sleep(1)

            task = self.generate_image(
                prompt=prompt,
                output_path=output_path,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                seed=seed_start + i
            )
            tasks.append(task)

        # Generate images with limited concurrency
        results = []
        for task in tasks:
            result = await task
            results.append(result)

        return results
