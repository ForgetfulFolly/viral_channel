import os
import json
from typing import Optional, Dict, List
import openai
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader
from src.config import LLMConfig, LLMProviderConfig
import logging

# Configure logging
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, config: LLMConfig) -> None:
        """Initialize with LLM configuration."""
        self.config = config
        # Initialize OpenAI clients for primary and fallback providers
        self.primary_client = openai.AsyncOpenAI(
            base_url=config.primary.base_url,
            api_key=os.getenv('OPENAI_API_KEY', config.primary.api_key)
        )
        if config.fallback:
            self.fallback_client = openai.AsyncOpenAI(
                base_url=config.fallback.base_url,
                api_key=os.getenv('OPENAI_API_KEY_FALLBACK', config.fallback.api_key)
            )

    async def _send_request(self, client: openai.AsyncOpenAI, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Send a request to the LLM and return the response."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat.completions.create(
                model=self.config.primary.model_name,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error sending request: {e}")
            raise

    async def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Send a chat completion request and return the text response."""
        for attempt in range(self.config.max_attempts):
            try:
                response = await self._send_request(self.primary_client, prompt, system_prompt, **kwargs)
                return response
            except Exception as e:
                logger.warning(f"Primary provider failed on attempt {attempt + 1}: {e}")
                if not self.config.fallback or attempt == self.config.max_attempts - 1:
                    raise

        # Fallback to secondary provider if primary fails
        try:
            response = await self._send_request(self.fallback_client, prompt, system_prompt, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Fallback provider failed: {e}")
            raise

    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        """Parse the response as JSON, retries on failure up to 3 times."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response_text = await self.complete(prompt, system_prompt, **kwargs)
                return json.loads(response_text)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"JSON parsing failed on attempt {attempt + 1}: {e}")
                if schema:
                    corrective_prompt = f"The previous response was not valid JSON. Please provide a valid JSON response following this schema: {schema}"
                    prompt += f"\n\n{corrective_prompt}"

        raise ValueError("Failed to parse JSON after multiple attempts")

    async def classify(self, text: str, categories: List[str], **kwargs) -> str:
        """Return one of the provided categories based on the text."""
        system_prompt = "You are a classifier. Classify the following text into one of the given categories."
        prompt = f"Text: {text}\nCategories: {', '.join(categories)}"
        response = await self.complete(prompt, system_prompt, **kwargs)
        if response in categories:
            return response
        raise ValueError(f"Response '{response}' is not a valid category. Expected one of: {categories}")

    async def summarize(self, text: str, max_length: int = 200, **kwargs) -> str:
        """Summarize the text with a maximum length constraint."""
        system_prompt = "You are a summarizer. Summarize the following text in a concise manner."
        prompt = f"Text: {text}\nMax Length: {max_length}"
        response = await self.complete(prompt, system_prompt, **kwargs)
        if len(response) <= max_length:
            return response
        raise ValueError(f"Summarized text exceeds maximum length of {max_length} characters.")


class PromptManager:
    def __init__(self, template_dir: str = "config/prompts/") -> None:
        """Initialize with template directory path."""
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False
        )

    def load_prompt(self, template_name: str, **variables) -> str:
        """Load and render a Jinja2 template with variables."""
        try:
            template = self.env.get_template(template_name)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Error loading prompt {template_name}: {e}")
            raise