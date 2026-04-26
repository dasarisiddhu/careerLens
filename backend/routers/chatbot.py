# ============================================================
# CareerLens – Honest Career Coach Router
# File: backend/routers/chatbot.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from middleware.auth import get_authenticated_user, get_user_profile
from services.gemini_service import call_groq
from database import supabase
from config import settings
import uuid, logging

logger = logging.getLogger("careerlens.chatbot")
router = APIRouter()

HONEST_CAREER_COACH_PROMPT = """You are a brutally honest, no-nonsense senior technical career coach with 15+ years of experience in the tech industry. You do not sugarcoat. You do not ask the user how they feel. You are not a therapist or a friend.

Your job is to:
- Evaluate the user's skills, resume, GitHub, and career choices with ruthless honesty
- Tell them exactly what is wrong and why they are not competitive yet
- Give them a precise, actionable plan with specific technologies, timelines, and measurable goals
- Challenge weak excuses and vague goals immediately
- Compare them to actual market standards, not motivational benchmarks

Tone: Direct, demanding, occasionally sarcastic when the user is being lazy or unrealistic. Think of a mix between a strict engineering manager and a competitive programming mentor.

Do NOT: ask "How are you feeling about this?", give empty encouragement, say "Great question!", or soften critical feedback with excessive praise.

DO: Give specific feedback like "Your GitHub has 3 repos with no README and no deployed projects - this will get you rejected before an interview." or "You listed Python as a skill but your projects show no actual Python work. Fix this."
"""


class MessageRequest(BaseModel):
    content: str
    session_id: str | None = None


@router.post("/message")
async def send_message(body: MessageRequest, profile=Depends(get_user_profile)):
    """Send a message to the Honest Career Coach and get a response."""
    user_id = profile["user_id"]

    # Freemium message limit
    if profile["plan_type"] == "freemium" and profile["chatbot_message_count"] >= settings.FREEMIUM_MAX_CHATBOT_MSGS:
        raise HTTPException(status_code=403, detail="Honest Career Coach message limit reached. Upgrade to Premium for unlimited access.")

    session_id = body.session_id or str(uuid.uuid4())

    # Fetch conversation history for context
    history_res = supabase.table("chatbot_messages").select("role,content").eq("user_id", user_id).eq("session_id", session_id).order("created_at").execute()
    history = history_res.data or []

    # Get AI response
    messages = [{"role": "system", "content": HONEST_CAREER_COACH_PROMPT}]
    for msg in history[-8:]:
        messages.append({
            "role": "user" if msg["role"] == "user" else "assistant",
            "content": msg["content"],
        })
    messages.append({"role": "user", "content": body.content})
    reply = await call_groq(messages, temperature=0.7)

    # Persist both messages
    supabase.table("chatbot_messages").insert([
        {"user_id": user_id, "session_id": session_id, "role": "user", "content": body.content},
        {"user_id": user_id, "session_id": session_id, "role": "assistant", "content": reply},
    ]).execute()

    supabase.rpc("increment_chatbot_count", {"p_user_id": user_id}).execute()

    return {"success": True, "session_id": session_id, "reply": reply}


@router.get("/history")
async def get_chat_history(session_id: str | None = None, user=Depends(get_authenticated_user)):
    """Return chat sessions or messages for a specific session."""
    query = supabase.table("chatbot_messages").select("*").eq("user_id", user["user_id"])
    if session_id:
        query = query.eq("session_id", session_id)
    result = query.order("created_at").execute()
    return {"success": True, "messages": result.data}


@router.delete("/history/{session_id}")
async def clear_session(session_id: str, user=Depends(get_authenticated_user)):
    """Delete all messages in a chat session."""
    supabase.table("chatbot_messages").delete().eq("user_id", user["user_id"]).eq("session_id", session_id).execute()
    return {"success": True, "message": "Session cleared."}
