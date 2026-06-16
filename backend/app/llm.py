import json
import logging
import boto3
from typing import AsyncGenerator, List, Dict, Any
from anthropic import AsyncAnthropic
from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        if self.provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                logger.warning("Anthropic API key is not set, API calls might fail if client is not configured.")
            self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        elif self.provider == "bedrock":
            # Boto3 client uses AWS credential chain (IAM roles, environment vars, etc.)
            self.bedrock_client = boto3.client(
                service_name="bedrock-runtime",
                region_name=settings.AWS_REGION
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    async def stream_chat(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str = "You are a helpful AI assistant."
    ) -> AsyncGenerator[str, None]:
        """
        Streams response from Claude via the chosen provider (Bedrock or Anthropic).
        messages format: [{"role": "user"|"assistant", "content": "text"}]
        """
        if self.provider == "anthropic":
            async for chunk in self._stream_anthropic(messages, system_prompt):
                yield chunk
        elif self.provider == "bedrock":
            async for chunk in self._stream_bedrock(messages, system_prompt):
                yield chunk

    async def _stream_anthropic(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str
    ) -> AsyncGenerator[str, None]:
        try:
            # Map messages to Anthropic format
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            async with self.anthropic_client.messages.stream(
                model=settings.ANTHROPIC_MODEL_ID,
                max_tokens=4096,
                system=system_prompt,
                messages=formatted_messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Error in Anthropic streaming: {e}")
            yield f"Error: Failed to fetch response from Anthropic. Details: {str(e)}"

    async def _stream_bedrock(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str
    ) -> AsyncGenerator[str, None]:
        """
        Uses AWS Bedrock ConverseStream API to interact with Claude.
        This provides a standard interface for message structure.
        """
        try:
            # Format messages for Bedrock Converse API
            bedrock_messages = []
            for msg in messages:
                # Converse API expects "user" or "assistant" role
                role = msg["role"]
                # In Converse API, content must be a list of block elements (like text)
                bedrock_messages.append({
                    "role": role,
                    "content": [{"text": msg["content"]}]
                })

            # System prompt configuration
            system_config = [{"text": system_prompt}]

            # Run in executor because boto3 ConverseStream is a blocking call
            import anyio
            
            def call_converse_stream():
                return self.bedrock_client.converse_stream(
                    modelId=settings.BEDROCK_MODEL_ID,
                    messages=bedrock_messages,
                    system=system_config,
                    inferenceConfig={
                        "maxTokens": 4096,
                        "temperature": 0.7
                    }
                )

            # Await the blocking call using anyio to avoid blocking the event loop
            response = await anyio.to_thread.run_sync(call_converse_stream)
            stream = response.get("stream")
            
            if stream:
                for event in stream:
                    # Parse the stream event
                    # converse_stream yields events like 'messageStart', 'contentBlockStart', 'contentBlockDelta', etc.
                    if "contentBlockDelta" in event:
                        delta = event["contentBlockDelta"]["delta"]
                        if "text" in delta:
                            yield delta["text"]
        except Exception as e:
            logger.error(f"Error in Bedrock streaming: {e}")
            yield f"Error: Failed to fetch response from AWS Bedrock. Details: {str(e)}"
