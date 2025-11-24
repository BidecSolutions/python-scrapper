"""LLM client implementations for different providers"""
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class BaseLLMClient:
    """Base class for LLM clients"""
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Optional[str]:
        """
        Send messages to LLM and return response
        
        Args:
            messages: List of message dicts with "role" and "content"
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Response text, or None if error
        """
        raise NotImplementedError


# OpenAI Implementation
try:
    from openai import AsyncOpenAI
    
    class OpenAILLMClient(BaseLLMClient):
        """OpenAI GPT client"""
        
        def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
            """
            Initialize OpenAI client
            
            Args:
                api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
                model: Model to use (gpt-4o-mini, gpt-4, etc.)
            """
            import os
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key required")
            
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.model = model
        
        async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.1,
            **kwargs
        ) -> Optional[str]:
            """Call OpenAI chat completion"""
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},  # Force JSON output
                    **kwargs
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI API error: {e}", exc_info=True)
                return None

except ImportError:
    logger.warning("OpenAI library not installed. Install with: pip install openai")
    OpenAILLMClient = None


# Anthropic Implementation
try:
    import anthropic
    
    class AnthropicLLMClient(BaseLLMClient):
        """Anthropic Claude client"""
        
        def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
            """
            Initialize Anthropic client
            
            Args:
                api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
                model: Model to use (claude-3-haiku-20240307, claude-3-opus-20240229, etc.)
            """
            import os
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("Anthropic API key required")
            
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            self.model = model
        
        async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.1,
            max_tokens: int = 4096,
            **kwargs
        ) -> Optional[str]:
            """Call Anthropic messages API"""
            try:
                # Convert OpenAI format to Anthropic format
                anthropic_messages = []
                system_message = None
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        anthropic_messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                
                response = await self.client.messages.create(
                    model=self.model,
                    messages=anthropic_messages,
                    system=system_message or "",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Extract text from response
                if response.content and len(response.content) > 0:
                    return response.content[0].text
                return None
            
            except Exception as e:
                logger.error(f"Anthropic API error: {e}", exc_info=True)
                return None

except ImportError:
    logger.warning("Anthropic library not installed. Install with: pip install anthropic")
    AnthropicLLMClient = None


# Groq Implementation (Fast & Free)
try:
    from groq import AsyncGroq
    
    class GroqLLMClient(BaseLLMClient):
        """Groq client (fast inference)"""
        
        def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-70b-versatile"):
            """
            Initialize Groq client
            
            Args:
                api_key: Groq API key (defaults to GROQ_API_KEY env var)
                model: Model to use (llama-3.1-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768, etc.)
            """
            import os
            self.api_key = api_key or os.getenv("GROQ_API_KEY")
            if not self.api_key:
                raise ValueError("Groq API key required")
            
            self.client = AsyncGroq(api_key=self.api_key)
            self.model = model
        
        async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.1,
            **kwargs
        ) -> Optional[str]:
            """Call Groq chat completion"""
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},  # Force JSON output
                    **kwargs
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Groq API error: {e}", exc_info=True)
                return None

except ImportError:
    logger.warning("Groq library not installed. Install with: pip install groq")
    GroqLLMClient = None

