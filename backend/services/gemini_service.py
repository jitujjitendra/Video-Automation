"""Google Gemini API integration service."""

import asyncio
import json
import re
from typing import Any, Optional

import google.generativeai as genai


class GeminiService:
    """Service for interacting with Google Gemini API."""

    def __init__(self, api_key: str):
        """Initialize Gemini service with API key.

        Args:
            api_key: Google Gemini API key.
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")

    @staticmethod
    async def validate_key(api_key: str) -> tuple[bool, str]:
        """Validate a Gemini API key by making a test request.

        Args:
            api_key: API key to validate.

        Returns:
            Tuple of (is_valid, message).
        """
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-pro")
            # Make a simple test request
            response = await asyncio.to_thread(
                model.generate_content, "Say 'API key is valid' in exactly those words."
            )
            if response and response.text:
                return True, "API key is valid and working."
            return False, "API key validation failed - no response received."
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
                return False, "Invalid API key. Please check your key and try again."
            if "PERMISSION_DENIED" in error_msg:
                return False, "Permission denied. Please ensure your API key has the correct permissions."
            if "QUOTA_EXCEEDED" in error_msg:
                return True, "API key is valid but quota exceeded. Please try again later."
            return False, f"Validation error: {error_msg}"

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_retries: int = 3,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Gemini API.

        Args:
            prompt: The user prompt to generate from.
            system_instruction: Optional system instruction to guide the model.
            max_retries: Number of retry attempts on failure.
            temperature: Creativity parameter (0.0 to 1.0).

        Returns:
            Generated text response.

        Raises:
            Exception: If all retries fail.
        """
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=8192,
        )

        # If system instruction provided, prepend it to the prompt
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        last_error = None
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    full_prompt,
                    generation_config=generation_config,
                )

                if response and response.text:
                    return response.text

                raise ValueError("Empty response from Gemini API")

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)

        raise Exception(f"Failed after {max_retries} retries. Last error: {last_error}")

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_retries: int = 3,
        temperature: float = 0.7,
    ) -> Any:
        """Generate structured JSON output using Gemini API.

        Args:
            prompt: The user prompt to generate from.
            system_instruction: Optional system instruction to guide the model.
            max_retries: Number of retry attempts on failure.
            temperature: Creativity parameter (0.0 to 1.0).

        Returns:
            Parsed JSON data.

        Raises:
            Exception: If all retries fail or JSON parsing fails.
        """
        # Add JSON instruction to system prompt
        json_instruction = (
            "You MUST respond with valid JSON only. No markdown code blocks, "
            "no extra text before or after the JSON. Just pure JSON."
        )
        if system_instruction:
            system_instruction = f"{system_instruction}\n\n{json_instruction}"
        else:
            system_instruction = json_instruction

        last_error = None
        for attempt in range(max_retries):
            try:
                text = await self.generate_text(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    max_retries=1,  # Handle retries at this level
                    temperature=temperature,
                )

                # Try to extract JSON from the response
                json_data = self._extract_json(text)
                return json_data

            except json.JSONDecodeError as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise Exception(f"Failed to generate valid JSON after {max_retries} retries. Last error: {last_error}")

    @staticmethod
    def _extract_json(text: str) -> Any:
        """Extract JSON from text that may contain markdown code blocks.

        Args:
            text: Raw text that may contain JSON.

        Returns:
            Parsed JSON data.
        """
        # Remove markdown code blocks if present
        text = text.strip()

        # Try to find JSON in code blocks
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1).strip()

        # Try direct parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object or array in the text
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start_idx = text.find(start_char)
            if start_idx != -1:
                # Find the matching closing bracket
                depth = 0
                for i in range(start_idx, len(text)):
                    if text[i] == start_char:
                        depth += 1
                    elif text[i] == end_char:
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(text[start_idx : i + 1])
                            except json.JSONDecodeError:
                                break

        raise json.JSONDecodeError("No valid JSON found in response", text, 0)
