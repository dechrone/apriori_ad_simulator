"""OpenRouter API client with tiered routing (Gemini Pro/Flash via OpenRouter)."""

import asyncio
import json
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import AsyncOpenAI

from src.utils.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    GEMINI_PRO_MODEL,
    GEMINI_FLASH_MODEL,
    GENERATION_CONFIG,
    MAX_CONCURRENT_REQUESTS
)


class GeminiClient:
    """Unified Gemini API client with tier routing via OpenRouter."""
    
    def __init__(self):
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment")
        
        # Initialize OpenAI client pointing to OpenRouter
        self.client = AsyncOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL
        )
        
        self.pro_model = GEMINI_PRO_MODEL
        self.flash_model = GEMINI_FLASH_MODEL
        
        # OpenRouter-specific headers
        self.extra_headers = {
            "HTTP-Referer": "https://apriori.ai",  # Replace with your site
            "X-Title": "Apriori Ad Simulator"
        }
        
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_pro(self, prompt: str, image_data: Optional[bytes] = None, system_prompt: Optional[str] = None) -> str:
        """Generate using Gemini Pro (Tier 1 - High Fidelity) via OpenRouter.
        
        Args:
            prompt: The user message/task
            image_data: Optional image bytes for multimodal input
            system_prompt: Optional system message to set context/role
        """
        async with self.semaphore:
            try:
                messages = []
                
                # Add system message if provided (for persona simulation, this sets the role)
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                
                if image_data:
                    # OpenRouter supports image input via base64
                    import base64
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    })
                else:
                    messages.append({
                        "role": "user",
                        "content": prompt
                    })
                
                response = await self.client.chat.completions.create(
                    model=self.pro_model,
                    messages=messages,
                    temperature=GENERATION_CONFIG.get("temperature", 0.7),
                    max_tokens=GENERATION_CONFIG.get("max_output_tokens", 2048),
                    extra_headers=self.extra_headers
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ OpenRouter API error (Pro): {error_msg}")
                if "model" in error_msg.lower():
                    print(f"   Model '{self.pro_model}' might not be available. Check OpenRouter.ai for available models.")
                raise RuntimeError(f"OpenRouter API error (Pro): {error_msg}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_flash(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using Gemini Flash (Tier 2 - High Throughput) via OpenRouter.
        
        Args:
            prompt: The user message/task
            system_prompt: Optional system message to set context/role
        """
        async with self.semaphore:
            try:
                messages = []
                
                # Add system message if provided (for persona simulation, this sets the role)
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                
                messages.append({
                    "role": "user",
                    "content": prompt
                })
                
                response = await self.client.chat.completions.create(
                    model=self.flash_model,
                    messages=messages,
                    temperature=GENERATION_CONFIG.get("temperature", 0.7),
                    max_tokens=GENERATION_CONFIG.get("max_output_tokens", 2048),
                    extra_headers=self.extra_headers
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                raise RuntimeError(f"OpenRouter API error (Flash): {str(e)}")
    
    async def batch_generate_flash(self, prompts: List[str]) -> List[str]:
        """Batch generate using Flash for high throughput."""
        tasks = [self.generate_flash(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response with fallback parsing."""
        if not response:
            raise ValueError("Empty response from API")
            
        # Try to find JSON in markdown code blocks
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()
        
        # Clean up common JSON issues
        # Replace newlines within strings with spaces
        import re
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Try to fix common issues
            try:
                # Remove invalid control characters
                json_str_cleaned = json_str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                # Remove multiple spaces
                json_str_cleaned = re.sub(r'\s+', ' ', json_str_cleaned)
                return json.loads(json_str_cleaned)
            except:
                pass
            
            # Fallback: try to extract from raw response even if it has extra text
            # Find first { and last }
            try:
                start_idx = response.find('{')
                end_idx = response.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx+1]
                    # Clean it
                    json_str = json_str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                    json_str = re.sub(r'\s+', ' ', json_str)
                    return json.loads(json_str)
            except:
                pass
            
            raise ValueError(f"Failed to parse JSON from response. Error: {str(e)}. Response preview: {response[:300]}")


# Global singleton
gemini_client = GeminiClient()
