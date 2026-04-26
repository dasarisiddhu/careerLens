# ============================================================
# CareerLens – Community Feed Router
# File: backend/routers/community.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from middleware.auth import get_authenticated_user
from database import supabase
import logging

logger = logging.getLogger("careerlens.community")
router = APIRouter()


# ============================================================
# Models
# ============================================================

class CreatePostRequest(BaseModel):
    post_type: str  # project / job / funding / blog / hiring
    title: str
    content: str
    demo_url: Optional[str] = ""
    github_url: Optional[str] = ""
    tags: Optional[List[str]] = []


class CreateCommentRequest(BaseModel):
    post_id: str
    content: str


# ============================================================
# Get all posts (feed)
# ============================================================

@router.get("/posts")
async def get_posts(
    post_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_authenticated_user)
):
    query = supabase.table("community_posts").select("*").order("created_at", desc=True).range(offset, offset + limit - 1)
    if post_type and post_type != "all":
        query = query.eq("post_type", post_type)
    result = query.execute()
    return {"success": True, "posts": result.data}


# ============================================================
# Create post
# ============================================================

@router.post("/posts")
async def create_post(body: CreatePostRequest, user=Depends(get_authenticated_user)):
    if not body.title.strip() or not body.content.strip():
        raise HTTPException(status_code=400, detail="Title and content are required.")

    # Get author name from users table
    try:
        profile = supabase.table("users").select("full_name").eq("user_id", user["user_id"]).single().execute()
        author_name = profile.data.get("full_name") or user.get("email", "Anonymous")
    except Exception:
        author_name = user.get("email", "Anonymous")

    result = supabase.table("community_posts").insert({
        "user_id": user["user_id"],
        "author_name": author_name,
        "author_email": user.get("email", ""),
        "post_type": body.post_type,
        "title": body.title.strip(),
        "content": body.content.strip(),
        "demo_url": body.demo_url or "",
        "github_url": body.github_url or "",
        "tags": body.tags or [],
    }).execute()

    return {"success": True, "post": result.data[0] if result.data else {}}


# ============================================================
# Delete post
# ============================================================

@router.delete("/posts/{post_id}")
async def delete_post(post_id: str, user=Depends(get_authenticated_user)):
    result = supabase.table("community_posts").select("user_id").eq("id", post_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Post not found.")
    if result.data["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own posts.")
    supabase.table("community_posts").delete().eq("id", post_id).execute()
    return {"success": True}


# ============================================================
# Like / Unlike post
# ============================================================

@router.post("/posts/{post_id}/like")
async def like_post(post_id: str, user=Depends(get_authenticated_user)):
    # Check if already liked
    existing = supabase.table("post_likes").select("id").eq("post_id", post_id).eq("user_id", user["user_id"]).execute()

    if existing.data:
        # Unlike
        supabase.table("post_likes").delete().eq("post_id", post_id).eq("user_id", user["user_id"]).execute()
        supabase.table("community_posts").update({"likes_count": supabase.raw("likes_count - 1")}).eq("id", post_id).execute()
        return {"success": True, "liked": False}
    else:
        # Like
        supabase.table("post_likes").insert({"post_id": post_id, "user_id": user["user_id"]}).execute()
        supabase.table("community_posts").update({"likes_count": supabase.raw("likes_count + 1")}).eq("id", post_id).execute()
        return {"success": True, "liked": True}


# ============================================================
# Get likes for user
# ============================================================

@router.get("/likes")
async def get_user_likes(user=Depends(get_authenticated_user)):
    result = supabase.table("post_likes").select("post_id").eq("user_id", user["user_id"]).execute()
    liked_ids = [r["post_id"] for r in result.data]
    return {"success": True, "liked_post_ids": liked_ids}


# ============================================================
# Get comments
# ============================================================

@router.get("/posts/{post_id}/comments")
async def get_comments(post_id: str, user=Depends(get_authenticated_user)):
    result = supabase.table("post_comments").select("*").eq("post_id", post_id).order("created_at", desc=False).execute()
    return {"success": True, "comments": result.data}


# ============================================================
# Add comment
# ============================================================

@router.post("/comments")
async def add_comment(body: CreateCommentRequest, user=Depends(get_authenticated_user)):
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty.")

    try:
        profile = supabase.table("users").select("full_name").eq("user_id", user["user_id"]).single().execute()
        author_name = profile.data.get("full_name") or user.get("email", "Anonymous")
    except Exception:
        author_name = user.get("email", "Anonymous")

    result = supabase.table("post_comments").insert({
        "post_id": body.post_id,
        "user_id": user["user_id"],
        "author_name": author_name,
        "content": body.content.strip(),
    }).execute()

    # Increment comment count
    supabase.table("community_posts").update({"comments_count": supabase.raw("comments_count + 1")}).eq("id", body.post_id).execute()

    return {"success": True, "comment": result.data[0] if result.data else {}}


# ============================================================
# Delete comment
# ============================================================

@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, user=Depends(get_authenticated_user)):
    result = supabase.table("post_comments").select("user_id, post_id").eq("id", comment_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if result.data["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own comments.")

    post_id = result.data["post_id"]
    supabase.table("post_comments").delete().eq("id", comment_id).execute()
    supabase.table("community_posts").update({"comments_count": supabase.raw("comments_count - 1")}).eq("id", post_id).execute()
    return {"success": True}
