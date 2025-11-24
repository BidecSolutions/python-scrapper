"""Factory for creating LLM clients from configuration"""
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def create_llm_client(provider: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
    """
    Create LLM client from configuration
    
    Args:
        provider: Provider name ("groq", "openai", "anthropic"). If None, auto-detect from env vars
        api_key: API key (optional, uses env vars if not provided)
        model: Model name (optional, uses default if not provided)
    
    Returns:
        LLM client instance, or None if no provider configured
    """
    # Auto-detect provider if not specified
    if not provider:
        if settings.GROQ_API_KEY:
            provider = "groq"
        elif settings.OPENAI_API_KEY:
            provider = "openai"
        elif settings.ANTHROPIC_API_KEY:
            provider = "anthropic"
        else:
            logger.warning("No LLM API key found in environment. AI extraction will be disabled.")
            return None
    
    # Create client based on provider
    if provider.lower() == "groq":
        try:
            from app.ai.llm_clients import GroqLLMClient
            if GroqLLMClient is None:
                logger.error("Groq client not available. Install with: pip install groq")
                return None
            key = api_key or settings.GROQ_API_KEY
            if not key:
                logger.error("Groq API key not found")
                return None
            return GroqLLMClient(
                api_key=key,
                model=model or "llama-3.1-70b-versatile"
            )
        except Exception as e:
            logger.error(f"Error creating Groq client: {e}")
            return None
    
    elif provider.lower() == "openai":
        try:
            from app.ai.llm_clients import OpenAILLMClient
            if OpenAILLMClient is None:
                logger.error("OpenAI client not available. Install with: pip install openai")
                return None
            key = api_key or settings.OPENAI_API_KEY
            if not key:
                logger.error("OpenAI API key not found")
                return None
            return OpenAILLMClient(
                api_key=key,
                model=model or "gpt-4o-mini"
            )
        except Exception as e:
            logger.error(f"Error creating OpenAI client: {e}")
            return None
    
    elif provider.lower() == "anthropic":
        try:
            from app.ai.llm_clients import AnthropicLLMClient
            if AnthropicLLMClient is None:
                logger.error("Anthropic client not available. Install with: pip install anthropic")
                return None
            key = api_key or settings.ANTHROPIC_API_KEY
            if not key:
                logger.error("Anthropic API key not found")
                return None
            return AnthropicLLMClient(
                api_key=key,
                model=model or "claude-3-haiku-20240307"
            )
        except Exception as e:
            logger.error(f"Error creating Anthropic client: {e}")
            return None
    
    else:
        logger.error(f"Unknown LLM provider: {provider}")
        return None

