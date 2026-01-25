"""Ad copy extraction using vision models."""

import asyncio
from tenacity import RetryError
from pathlib import Path
from typing import Optional

from src.api.gemini_client import gemini_client


async def extract_ad_copy_from_image(image_path: str) -> str:
    """Extract text/copy from ad image using Gemini Pro vision."""
    
    print(f"   📸 Extracting copy from: {Path(image_path).name}")
    
    try:
        # Load image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        prompt = """You are analyzing an advertising creative image.

Extract ALL TEXT visible in this ad image.

Include:
- Main headline
- Subheadline
- Body copy
- Call-to-action
- Any other visible text

Return the text in a natural reading order. If there's no text, return "No text found in image".
"""
        
        response = await gemini_client.generate_pro(prompt, image_data)
        
        # Clean up the response
        copy = response.strip()
        
        if copy and "no text" not in copy.lower():
            print(f"   ✅ Extracted: {copy[:80]}...")
            return copy
        else:
            print(f"   ⚠️ No text found in image")
            return ""
            
    except RetryError as e:
        last_exc = e.last_attempt.exception() if e.last_attempt else None
        if last_exc:
            print(f"   ❌ Error extracting copy (retry exhausted): {last_exc}")
        else:
            print(f"   ❌ Error extracting copy (retry exhausted): {e}")
        return ""
    except Exception as e:
        print(f"   ❌ Error extracting copy: {e}")
        return ""


async def extract_copy_for_all_ads(ads_dir: Path) -> dict:
    """Extract copy from all ad images in a directory."""
    
    ad_files = sorted(ads_dir.glob("*.jpeg")) + sorted(ads_dir.glob("*.jpg")) + sorted(ads_dir.glob("*.png"))
    
    if not ad_files:
        print("❌ No ad images found in ads/ folder!")
        return {}
    
    print(f"\n📝 Extracting copy from {len(ad_files)} ad images...")
    print("-" * 80)
    
    copy_map = {}

    # Process sequentially to avoid rate-limit spikes
    for ad_file in ad_files:
        copy = await extract_ad_copy_from_image(str(ad_file))
        copy_map[str(ad_file)] = copy
        await asyncio.sleep(0.5)
    
    print("-" * 80)
    print(f"✅ Extraction complete\n")
    
    return copy_map
