import asyncio
import httpx
import json
from typing import Dict, Any, Optional
from config import config

class GeminiSentimentAnalyzer:
    def __init__(self, api_key=None):
        if api_key is None:
            self.api_key = config["gemini"]["api_key"]
        else:
            self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        self.system_instruction = "You are an AI that helps determine the sentiment of a conversation and if it should increase affection or decrease it."

    async def generate_structured_content(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        model_name: str = "gemini-2.0-flash",
    ) -> Optional[Dict[str, Any]]:
        """
        Generates content based on a prompt and a JSON schema.
        """
        url = self.base_url.format(api_key=self.api_key)
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "system_instruction": {"parts": [{"text": self.system_instruction}]},
            "generationConfig": {
                "response_mime_type": "application/json",
                "response_schema": response_schema,
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                print("Sending request to Gemini...")
                response = await client.post(url, json=payload, timeout=None)
                print(f"Gemini response status code: {response.status_code}")
                response.raise_for_status()
                response_json = response.json()

                # attmpt extract structured data
                try:
                    structured_data_text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                    structured_data = json.loads(structured_data_text)
                    print("Gemini structured data:", json.dumps(structured_data, indent=2))
                    return structured_data
                except (KeyError, IndexError, json.JSONDecodeError) as e:
                    print(f"Error extracting or parsing data: {e}. Full response:\n", json.dumps(response_json, indent=2))
                    return None

        except httpx.HTTPError as e:
            print(f"HTTP Error: {e}\nResponse: {e.response.text}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    async def analyze_sentiment(self, text: str) -> Optional[str]:
        """Analyzes the sentiment of the given text and returns 'positive', 'negative', or None."""
        response_schema = {
            "type": "object",
            "properties": {
                "sentiment_category": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral"],
                    "description": "Sentiment of the conversation (positive, negative, or neutral)",
                },
            },
            "required": ["sentiment_category"],
        }
        prompt = f"Analyze the sentiment of the following conversation, and determine if its positive negative, or neutral. Respond with 'positive', 'negative', or 'neutral'. Text: '{text}'"
        print("Prompt in analyze_sentiment:", prompt)

        structured_data = await self.generate_structured_content(prompt, response_schema)
        if structured_data:
            return structured_data.get("sentiment_category")
        else:
            return None
