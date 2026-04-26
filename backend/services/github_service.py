# ============================================================
# CareerLens – GitHub Service
# File: backend/services/github_service.py
# ============================================================

import asyncio
import httpx
from config import settings
from database import supabase
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger("careerlens.github")

GITHUB_API = "https://api.github.com"


def _headers():
    h = {"Accept": "application/vnd.github.v3+json"}
    if settings.GITHUB_TOKEN:
        h["Authorization"] = f"token {settings.GITHUB_TOKEN}"
    return h


async def fetch_github_profile(username: str) -> dict:
    """Fetch GitHub profile with caching (6hr TTL)."""
    # Check cache
    try:
        cached = supabase.table("github_cache").select("*").eq("github_username", username).single().execute()
        if cached.data:
            expires = datetime.fromisoformat(cached.data["expires_at"].replace("Z", "+00:00"))
            if expires > datetime.now(timezone.utc):
                return {**cached.data["profile_data"], "repos": cached.data["repos_data"], "languages": cached.data["languages_data"]}
    except Exception:
        pass

    async with httpx.AsyncClient(headers=_headers(), timeout=10) as client:
        # Fetch profile
        profile_res = await client.get(f"{GITHUB_API}/users/{username}")
        if profile_res.status_code == 404:
            raise ValueError(f"GitHub user '{username}' not found.")
        profile = profile_res.json()

        # Fetch repos
        repos_res = await client.get(f"{GITHUB_API}/users/{username}/repos", params={"sort": "stars", "per_page": 30})
        repos = repos_res.json() if repos_res.status_code == 200 else []

        readme_checked_repos = repos[:10]
        readme_results = await asyncio.gather(*[
            client.get(f"{GITHUB_API}/repos/{username}/{repo.get('name')}/readme")
            for repo in readme_checked_repos if repo.get("name")
        ], return_exceptions=True)
        readme_lookup = {}
        for repo, result in zip([repo for repo in readme_checked_repos if repo.get("name")], readme_results):
            readme_lookup[repo["name"]] = isinstance(result, httpx.Response) and result.status_code == 200

        # Aggregate languages
        languages: dict = {}
        total_stars = 0
        repo_summaries = []
        original_repos = 0
        forked_repos = 0
        recent_active_repos = 0
        recent_active_repos_30d = 0
        deployed_repos = 0
        repos_with_readme = 0
        last_activity_at = ""
        recent_cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=180)
        for repo in repos[:15]:
            total_stars += repo.get("stargazers_count", 0)
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            has_readme = bool(readme_lookup.get(repo.get("name", ""), False))
            if has_readme:
                repos_with_readme += 1
            if repo.get("homepage") or repo.get("has_pages"):
                deployed_repos += 1
            if repo.get("fork"):
                forked_repos += 1
            else:
                original_repos += 1
            activity_at = repo.get("pushed_at") or repo.get("updated_at")
            if activity_at:
                try:
                    updated_dt = datetime.fromisoformat(activity_at.replace("Z", "+00:00"))
                    if updated_dt >= recent_cutoff_30d:
                        recent_active_repos_30d += 1
                    if updated_dt >= recent_cutoff:
                        recent_active_repos += 1
                    if not last_activity_at or updated_dt.isoformat() > last_activity_at:
                        last_activity_at = updated_dt.isoformat()
                except Exception:
                    pass
            repo_summaries.append({
                "name": repo["name"],
                "description": repo.get("description", ""),
                "stars": repo.get("stargazers_count", 0),
                "language": lang,
                "url": repo.get("html_url", ""),
                "updated_at": repo.get("updated_at", ""),
                "pushed_at": repo.get("pushed_at", ""),
                "fork": bool(repo.get("fork")),
                "has_readme": has_readme,
                "has_pages": bool(repo.get("has_pages")),
                "homepage": repo.get("homepage", "") or "",
            })

    repo_count = int(profile.get("public_repos", len(repos) if isinstance(repos, list) else 0) or 0)
    github_score = 80
    # Honest scoring: empty/inactive GitHub is a major red flag
    # Do not give high scores to profiles with:
    # - Fewer than 5 repos
    # - No commits in last 6 months
    # - Only forked repos, no original work
    # - No README files
    # Recruiters check GitHub. An empty profile hurts more than helps.
    if repo_count < 5:
        github_score -= 20
    elif repo_count < 10:
        github_score -= 10
    if recent_active_repos == 0:
        github_score -= 15
    if repo_count > 0 and original_repos == 0:
        github_score -= 15
    if readme_checked_repos and repos_with_readme == 0:
        github_score -= 12
    elif readme_checked_repos and repos_with_readme < max(1, len(readme_checked_repos) // 3):
        github_score -= 6
    if original_repos > 0 and deployed_repos == 0:
        github_score -= 8
    if recent_active_repos_30d == 0:
        github_score -= 6

    result = {
        "username": username,
        "name": profile.get("name", username),
        "bio": profile.get("bio", ""),
        "public_repos": profile.get("public_repos", 0),
        "followers": profile.get("followers", 0),
        "following": profile.get("following", 0),
        "avatar_url": profile.get("avatar_url", ""),
        "profile_url": profile.get("html_url", ""),
        "total_stars": total_stars,
        "activity_summary": f"{len(repos)} public repos, {total_stars} total stars, {original_repos} original, {forked_repos} forks",
        "github_score": max(0, min(100, github_score)),
        "forked_repos": forked_repos,
        "original_repos": original_repos,
        "repos_with_readme": repos_with_readme,
        "readme_checked_repos": len([repo for repo in readme_checked_repos if repo.get('name')]),
        "deployed_repos": deployed_repos,
        "recent_active_repos_30d": recent_active_repos_30d,
        "recent_active_repos": recent_active_repos,
        "last_activity_at": last_activity_at,
        "repos": repo_summaries,
        "languages": dict(sorted(languages.items(), key=lambda x: x[1], reverse=True)),
    }

    # Cache result
    try:
        supabase.table("github_cache").upsert({
            "github_username": username,
            "profile_data": {k: v for k, v in result.items() if k not in ["repos", "languages"]},
            "repos_data": repo_summaries,
            "languages_data": result["languages"],
        }).execute()
    except Exception as e:
        logger.warning(f"GitHub cache write failed: {e}")

    return result


async def get_github_data(username: str) -> dict:
    """
    Backward-compatible alias used by older routers.
    """
    return await fetch_github_profile(username)
