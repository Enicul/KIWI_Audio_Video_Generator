"""
Image Agent - Generates consistent first-frame images for video scenes
Uses Gemini Imagen to create visually consistent images across scenes
"""
from typing import Any, Dict, List, Optional
from pathlib import Path
import base64
import asyncio

from .base import BaseAgent


class ImageAgent(BaseAgent):
    """
    Agent responsible for generating consistent first-frame images.
    Creates images that will be used as starting frames for video generation.
    """
    
    def __init__(self):
        super().__init__(
            name="ImageAgent",
            description="Generates consistent first-frame images for scenes"
        )
        self.client = None
        self._initialized = False
        self.output_dir = Path("generated/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize(self, client):
        """Initialize with Gemini client"""
        self.client = client
        self._initialized = True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate first-frame images for all scenes with visual consistency.
        
        Input:
            scenes: List of scene descriptions
            visual_style: Global visual style for consistency
            task_id: Task identifier
            
        Output:
            success: bool
            images: List of image paths
            error: str (if failed)
        """
        scenes = input_data.get("scenes", [])
        visual_style = input_data.get("visual_style", {})
        task_id = input_data.get("task_id", "default")
        
        if not scenes:
            return {"success": False, "error": "No scenes provided"}
        
        if not self._initialized or not self.client:
            return {"success": False, "error": "ImageAgent not initialized"}
        
        try:
            from google.genai import types
            
            generated_images = []
            
            # Build consistent character/style description
            character_desc = visual_style.get("main_character", "a person")
            color_palette = visual_style.get("color_palette", "natural cinematic colors")
            lighting = visual_style.get("lighting", "natural lighting")
            visual_tone = visual_style.get("visual_tone", "realistic")
            
            # Base style prompt that will be consistent across all images
            style_base = f"""
Style requirements (MUST follow for ALL images):
- Character: {character_desc}
- Color palette: {color_palette}
- Lighting: {lighting}
- Visual tone: {visual_tone}
- Aspect ratio: 16:9 cinematic
- High quality, photorealistic
"""
            
            for i, scene in enumerate(scenes):
                scene_num = i + 1
                scene_desc = scene.get("description", scene.get("title", f"Scene {scene_num}"))
                
                await self.update_progress(
                    int(10 + (i / len(scenes)) * 30),
                    f"Generating first frame for scene {scene_num}/{len(scenes)}..."
                )
                
                # Combine scene description with style requirements
                image_prompt = f"""Generate a single high-quality still image for this scene:

Scene: {scene_desc}

{style_base}

Important: This is frame 1 of a video sequence. Make it look like a movie still.
The character must look EXACTLY as described - this is critical for visual consistency.
"""
                
                try:
                    # Use Imagen model for image generation
                    response = self.client.models.generate_images(
                        model="imagen-3.0-generate-002",
                        prompt=image_prompt,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            aspect_ratio="16:9",
                            safety_filter_level="BLOCK_ONLY_HIGH",
                        )
                    )
                    
                    if response and response.generated_images:
                        # Save the image
                        image_data = response.generated_images[0]
                        image_path = self.output_dir / f"{task_id}_scene{scene_num}_frame.png"
                        
                        # Get image bytes
                        if hasattr(image_data, 'image') and hasattr(image_data.image, 'image_bytes'):
                            image_bytes = image_data.image.image_bytes
                        elif hasattr(image_data, 'image_bytes'):
                            image_bytes = image_data.image_bytes
                        else:
                            # Try to decode from base64 if available
                            image_bytes = base64.b64decode(image_data.image.data) if hasattr(image_data.image, 'data') else None
                        
                        if image_bytes:
                            with open(image_path, "wb") as f:
                                f.write(image_bytes)
                            
                            generated_images.append({
                                "scene_number": scene_num,
                                "image_path": str(image_path),
                                "scene_description": scene_desc
                            })
                            
                            await self.send_message(f"✓ Scene {scene_num} first frame generated")
                        else:
                            print(f"[ImageAgent] Could not extract image bytes for scene {scene_num}")
                            generated_images.append({
                                "scene_number": scene_num,
                                "image_path": None,
                                "error": "Could not extract image bytes"
                            })
                    else:
                        print(f"[ImageAgent] No image generated for scene {scene_num}")
                        generated_images.append({
                            "scene_number": scene_num,
                            "image_path": None,
                            "error": "No image in response"
                        })
                        
                except Exception as e:
                    print(f"[ImageAgent] Scene {scene_num} image generation failed: {e}")
                    generated_images.append({
                        "scene_number": scene_num,
                        "image_path": None,
                        "error": str(e)
                    })
            
            # Check how many succeeded
            successful = [img for img in generated_images if img.get("image_path")]
            
            if not successful:
                return {
                    "success": False,
                    "error": "No images were generated successfully",
                    "images": generated_images
                }
            
            await self.update_progress(40, f"Generated {len(successful)}/{len(scenes)} first frames")
            
            return {
                "success": True,
                "images": generated_images,
                "successful_count": len(successful),
                "total_count": len(scenes)
            }
            
        except Exception as e:
            print(f"[ImageAgent] Error: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_single_image(
        self, 
        prompt: str, 
        task_id: str, 
        scene_num: int
    ) -> Optional[str]:
        """Generate a single image and return the path"""
        if not self._initialized or not self.client:
            return None
        
        try:
            from google.genai import types
            
            response = self.client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                )
            )
            
            if response and response.generated_images:
                image_data = response.generated_images[0]
                image_path = self.output_dir / f"{task_id}_scene{scene_num}_frame.png"
                
                if hasattr(image_data, 'image') and hasattr(image_data.image, 'image_bytes'):
                    with open(image_path, "wb") as f:
                        f.write(image_data.image.image_bytes)
                    return str(image_path)
            
            return None
            
        except Exception as e:
            print(f"[ImageAgent] Single image generation failed: {e}")
            return None


# Singleton instance
image_agent = ImageAgent()

