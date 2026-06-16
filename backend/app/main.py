import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.llm import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for AWS EKS Claude AI Chatbot",
    version="1.0.0"
)

# Configure CORS
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM Service
llm_service = None

@app.on_event("startup")
def startup_event():
    global llm_service
    try:
        llm_service = LLMService()
        logger.info(f"LLM Service initialized successfully with provider: {settings.LLM_PROVIDER}")
    except Exception as e:
        logger.error(f"Failed to initialize LLM Service: {e}")

# Request/Response schemas
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender: 'user' or 'assistant'")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="The chat history including the latest user message")
    system_prompt: Optional[str] = Field("You are a helpful AI assistant.", description="Custom system prompt for Claude")

class ProviderConfigResponse(BaseModel):
    provider: str
    model_id: str
    region: Optional[str] = None

@app.get("/api/health")
def health_check():
    """Simple health check endpoint for EKS liveness/readiness probes."""
    return {"status": "healthy", "provider": settings.LLM_PROVIDER}

@app.get("/api/config", response_model=ProviderConfigResponse)
def get_config():
    """Returns the current LLM configuration for display on the frontend."""
    if settings.LLM_PROVIDER == "bedrock":
        return {
            "provider": "AWS Bedrock",
            "model_id": settings.BEDROCK_MODEL_ID,
            "region": settings.AWS_REGION
        }
    else:
        return {
            "provider": "Anthropic Claude API",
            "model_id": settings.ANTHROPIC_MODEL_ID
        }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Accepts chat history and streams responses back using Server-Sent Events (SSE).
    """
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service is not initialized")

    # Basic input validation
    if not request.messages:
        raise HTTPException(status_code=400, detail="Message history cannot be empty")
    
    if request.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="The last message in history must be from the user")

    # Format messages for the service
    formatted_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    async def event_generator():
        try:
            async for chunk in llm_service.stream_chat(formatted_messages, request.system_prompt):
                # Yield SSE-formatted string
                yield {"data": chunk}
        except Exception as e:
            logger.error(f"Error generating chat stream: {e}")
            yield {"data": f"[ERROR: {str(e)}]"}

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG
    )
