from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
import uuid
from datetime import datetime

# Optional provider SDKs are imported lazily inside functions to avoid import errors when not installed

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (must use existing env vars only)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app and API router (all routes under /api)
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ----------------------------
# Models
# ----------------------------
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class Message(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str

class ResponseMeta(BaseModel):
    provider: str
    model: str
    usage: Optional[Dict[str, int]] = None
    processing_time: Optional[float] = None

class ChatRequest(BaseModel):
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 800

class ChatResponse(BaseModel):
    message: Message
    meta: ResponseMeta

# Story models
DEFAULT_SECTIONS = {
    "guidingNarrative": "",
    "turningPoints": "",
    "emergingThemes": "",
    "uniqueStrengths": "",
    "futureVision": "",
}

class Story(BaseModel):
    storyId: str
    clientId: str
    version: int = 1
    sections: Dict[str, str] = Field(default_factory=lambda: DEFAULT_SECTIONS.copy())
    resonanceScore: Optional[float] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    history: List[Dict[str, Any]] = Field(default_factory=list)

class StoryInitRequest(BaseModel):
    clientId: str

class StorySaveRequest(BaseModel):
    storyId: str
    clientId: str
    sections: Dict[str, str]
    resonanceScore: Optional[float] = None

# ----------------------------
# Helper functions
# ----------------------------

def _detect_provider() -> str:
    """Decide provider based on AI_PROVIDER env or available keys.
    Does not require adding new env vars; defaults safely.
    """
    provider_env = os.environ.get('AI_PROVIDER', '').strip().lower()
    openai_key = os.environ.get('OPENAI_API_KEY')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    google_key = os.environ.get('GOOGLE_API_KEY')

    allowed = {'openai', 'anthropic', 'gemini'}
    if provider_env in allowed:
        return provider_env

    # Fallback: pick first available
    if openai_key:
        return 'openai'
    if anthropic_key:
        return 'anthropic'
    if google_key:
        return 'gemini'

    return 'openai'  # default choice; will error at runtime if key missing

async def _generate_with_openai(messages: List[Message], temperature: float, max_tokens: int) -> ChatResponse:
    import time
    start = time.time()
    try:
        from openai import AsyncOpenAI  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI SDK not installed: {e}")

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=400, detail="Missing OPENAI_API_KEY in backend environment")

    model = os.environ.get('OPENAI_MODEL', 'gpt-4o')
    client = AsyncOpenAI(api_key=api_key)

    # Build message list with system safety prompt
    system_prompt = (
        "You are a supportive AI assistant for personal reflection and emotional well-being.\n"
        "- You are not a licensed clinician and do not provide medical advice.\n"
        "- Focus on reflective listening, validation, and open-ended questions.\n"
        "- Encourage reaching out to professionals or emergency resources in crisis."
    )
    openai_msgs = [{"role": "system", "content": system_prompt}] + [m.model_dump() for m in messages]

    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=openai_msgs,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = resp.choices[0].message.content or ""
        usage = None
        if getattr(resp, 'usage', None):
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens": resp.usage.total_tokens,
            }
        return ChatResponse(
            message=Message(role='assistant', content=content),
            meta=ResponseMeta(provider='openai', model=model, usage=usage, processing_time=time.time()-start)
        )
    except Exception as e:
        logger.exception("OpenAI generation failed")
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

async def _generate_with_anthropic(messages: List[Message], temperature: float, max_tokens: int) -> ChatResponse:
    import time
    start = time.time()
    try:
        from anthropic import AsyncAnthropic  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anthropic SDK not installed: {e}")

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise HTTPException(status_code=400, detail="Missing ANTHROPIC_API_KEY in backend environment")

    model = os.environ.get('ANTHROPIC_MODEL', 'claude-3.5-sonnet')
    client = AsyncAnthropic(api_key=api_key)

    system_prompt = (
        "You are a supportive AI assistant for personal reflection and emotional well-being.\n"
        "- You are not a licensed clinician and do not provide medical advice.\n"
        "- Focus on reflective listening, validation, and open-ended questions.\n"
        "- Encourage reaching out to professionals or emergency resources in crisis."
    )

    # Claude separates system from messages
    claude_messages = [m.model_dump() for m in messages if m.role != 'system']

    try:
        resp = await client.messages.create(
            model=model,
            system=system_prompt,
            messages=claude_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = resp.content[0].text if getattr(resp, 'content', None) else ""
        usage = None
        if getattr(resp, 'usage', None):
            usage = {
                "prompt_tokens": resp.usage.input_tokens,
                "completion_tokens": resp.usage.output_tokens,
                "total_tokens": resp.usage.input_tokens + resp.usage.output_tokens,
            }
        return ChatResponse(
            message=Message(role='assistant', content=content),
            meta=ResponseMeta(provider='anthropic', model=model, usage=usage, processing_time=time.time()-start)
        )
    except Exception as e:
        logger.exception("Anthropic generation failed")
        raise HTTPException(status_code=500, detail=f"Anthropic error: {e}")

async def _generate_with_gemini(messages: List[Message], temperature: float, max_tokens: int) -> ChatResponse:
    # Gemini support is optional in this environment; we try google-generativeai first.
    import time
    start = time.time()
    try:
        import google.generativeai as genai  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini SDK not installed: {e}")

    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=400, detail="Missing GOOGLE_API_KEY in backend environment")

    model_name = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    genai.configure(api_key=api_key)

    # Build a single prompt combining system and conversation
    system_prompt = (
        "You are a supportive AI assistant for personal reflection and emotional well-being.\n"
        "- You are not a licensed clinician and do not provide medical advice.\n"
        "- Focus on reflective listening, validation, and open-ended questions.\n"
        "- Encourage reaching out to professionals or emergency resources in crisis."
    )
    conv_text = [f"{m.role}: {m.content}" for m in messages]
    prompt = f"System: {system_prompt}\n\n" + "\n".join(conv_text)

    try:
        model = genai.GenerativeModel(model_name)
        resp = await model.generate_content_async(prompt, generation_config={
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        })
        content = resp.text or ""
        return ChatResponse(
            message=Message(role='assistant', content=content),
            meta=ResponseMeta(provider='gemini', model=model_name, usage=None, processing_time=time.time()-start)
        )
    except Exception as e:
        logger.exception("Gemini generation failed")
        raise HTTPException(status_code=500, detail=f"Gemini error: {e}")

async def generate_ai_response(payload: ChatRequest) -> ChatResponse:
    provider = _detect_provider()
    if provider == 'openai':
        return await _generate_with_openai(payload.messages, payload.temperature or 0.7, payload.max_tokens or 800)
    if provider == 'anthropic':
        return await _generate_with_anthropic(payload.messages, payload.temperature or 0.7, payload.max_tokens or 800)
    if provider == 'gemini':
        return await _generate_with_gemini(payload.messages, payload.temperature or 0.7, payload.max_tokens or 800)
    raise HTTPException(status_code=400, detail=f"Unsupported AI provider: {provider}")

# ----------------------------
# Routes - Health & Chat
# ----------------------------
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.get("/health")
async def health():
    provider = _detect_provider()
    return {"status": "ok", "provider": provider}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.model_dump())
    await db.status_checks.insert_one(status_obj.model_dump())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    items = await db.status_checks.find().to_list(1000)
    cleaned = []
    for it in items:
        it.pop('_id', None)  # avoid ObjectID serialization issues
        cleaned.append(StatusCheck(**it))
    return cleaned

@api_router.get("/provider-info")
async def provider_info():
    provider = _detect_provider()
    model = {
        'openai': os.environ.get('OPENAI_MODEL', 'gpt-4o'),
        'anthropic': os.environ.get('ANTHROPIC_MODEL', 'claude-3.5-sonnet'),
        'gemini': os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash'),
    }.get(provider, 'unknown')
    return {"provider": provider, "model": model, "available_providers": ["openai", "anthropic", "gemini"]}

@api_router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    # Basic validation
    if not payload.messages or payload.messages[0].role == 'assistant':
        raise HTTPException(status_code=400, detail="Conversation must start with a user/system message")
    return await generate_ai_response(payload)

# ----------------------------
# Routes - Story (MVP): init, save, get
# ----------------------------
@api_router.post("/story/init", response_model=Story)
async def story_init(req: StoryInitRequest):
    # Try to find existing story by clientId
    existing = await db.stories.find_one({"clientId": req.clientId})
    if existing:
        existing.pop('_id', None)
        return Story(**existing)
    # Create new
    story = Story(
        storyId=str(uuid.uuid4()),
        clientId=req.clientId,
        sections=DEFAULT_SECTIONS.copy(),
        version=1,
        resonanceScore=None,
    )
    await db.stories.insert_one(story.model_dump())
    return story

@api_router.put("/story/save", response_model=Story)
async def story_save(req: StorySaveRequest):
    doc = await db.stories.find_one({"storyId": req.storyId, "clientId": req.clientId})
    now = datetime.utcnow()
    if not doc:
        # Create if not exists
        story = Story(
            storyId=req.storyId or str(uuid.uuid4()),
            clientId=req.clientId,
            sections=req.sections or DEFAULT_SECTIONS.copy(),
            version=1,
            resonanceScore=req.resonanceScore,
            createdAt=now,
            updatedAt=now,
            history=[],
        )
        await db.stories.insert_one(story.model_dump())
        return story

    # Append to history minimal snapshot
    history_entry = {
        "version": doc.get("version", 1),
        "sections": doc.get("sections", {}),
        "resonanceScore": doc.get("resonanceScore"),
        "timestamp": doc.get("updatedAt", doc.get("createdAt", now)),
    }
    history = doc.get("history", [])
    history.append(history_entry)
    # Keep last 10 snapshots to limit size
    if len(history) > 10:
        history = history[-10:]

    new_version = int(doc.get("version", 1)) + 1
    update_doc = {
        "$set": {
            "sections": req.sections,
            "resonanceScore": req.resonanceScore,
            "updatedAt": now,
            "history": history,
            "version": new_version,
        }
    }
    await db.stories.update_one({"storyId": req.storyId, "clientId": req.clientId}, update_doc)
    updated = await db.stories.find_one({"storyId": req.storyId, "clientId": req.clientId})
    updated.pop('_id', None)
    return Story(**updated)

@api_router.get("/story/{story_id}", response_model=Story)
async def story_get(story_id: str):
    doc = await db.stories.find_one({"storyId": story_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Story not found")
    doc.pop('_id', None)
    return Story(**doc)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()