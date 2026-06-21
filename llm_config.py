"""
LLM Configuration with retry logic and timeout handling
"""
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

load_dotenv()

# Create a custom HTTPClient with proper timeout settings
def create_groq_client():
    """Create a ChatGroq client with optimized settings and retry logic"""
    # Configure HTTPClient with longer timeouts and connection pooling
    http_client = httpx.Client(
        timeout=60.0,  # 60 second timeout
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
        ),
    )
    
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.7,
        max_tokens=2048,
        http_client=http_client,
    )
    
    return llm


# Decorator for retry logic
def with_retry(func):
    """Decorator to add exponential backoff retry logic"""
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            Exception,  # Catch all exceptions
        )),
        reraise=True
    )
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# Single LLM instance to reuse
llm = create_groq_client()
