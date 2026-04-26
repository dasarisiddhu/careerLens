from fastapi import APIRouter, Depends
from pydantic import BaseModel
from middleware.auth import get_authenticated_user
from services.gemini_service import generate_beginner_roadmap

router = APIRouter()

class BeginnerRequest(BaseModel):
    background: str
    target_field: str
    hours_per_day: str
    timeline: str
    goal: str

@router.post("/roadmap")
async def get_beginner_roadmap(body: BeginnerRequest, user=Depends(get_authenticated_user)):
    roadmap = await generate_beginner_roadmap(
        background=body.background,
        target_field=body.target_field,
        hours_per_day=body.hours_per_day,
        timeline=body.timeline,
        goal=body.goal
    )
    return {"success": True, "roadmap": roadmap}