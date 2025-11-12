import os
from dotenv import find_dotenv, load_dotenv

from langchain_google_genai.chat_models import ChatGoogleGenerativeAI


# load .env file
_ = load_dotenv(find_dotenv())


def initialize_llm(temperature: float = 0.8, max_tokens: int = 4098) -> ChatGoogleGenerativeAI:
    """
    Initialize Gemini LLM with configuration
    
    Args:
        temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
    
    Returns:
        Configured ChatGoogleGenerativeAI instance
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash")

    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )
