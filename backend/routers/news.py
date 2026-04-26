# ============================================================
# CareerLens – News Router
# File: backend/routers/news.py
# ============================================================

from fastapi import APIRouter
import asyncio
import httpx, feedparser, logging, time
from contextlib import suppress
from config import settings

logger = logging.getLogger("careerlens.news")
router = APIRouter()

CACHE_TTL_SECONDS = 300
_NEWS_CACHE = {
    "tech": {"ts": 0.0, "articles": []},
    "hiring": {"ts": 0.0, "articles": []},
}

TECH_RSS_FEEDS = [
    "https://feeds.feedburner.com/TechCrunch",
    "https://www.theverge.com/rss/index.xml",
    "https://hnrss.org/frontpage",
]

HIRING_RSS_FEEDS = [
    "https://feeds.feedburner.com/venturebeat/SZYF",
    "https://hnrss.org/jobs",
]


def _from_feed(feed_url: str, body: str, limit: int = 10) -> list:
    try:
        feed = feedparser.parse(body)
        articles = []
        for entry in feed.entries[:limit]:
            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:300],
                "published": entry.get("published", ""),
                "source": feed.feed.get("title", feed_url),
            })
        return articles
    except Exception as e:
        logger.warning(f"RSS parse failed for {feed_url}: {e}")
        return []


def _dedupe_articles(articles: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for article in articles:
        key = (article.get("link", "").strip(), article.get("title", "").strip().lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(article)
    return deduped


def _get_cached(category: str) -> list | None:
    item = _NEWS_CACHE.get(category)
    if not item:
        return None
    if time.time() - item["ts"] < CACHE_TTL_SECONDS and item["articles"]:
        return item["articles"]
    return None


def _set_cached(category: str, articles: list):
    _NEWS_CACHE[category] = {"ts": time.time(), "articles": articles}


async def _fetch_single_rss(client: httpx.AsyncClient, url: str, limit: int) -> list:
    try:
        res = await client.get(url)
        res.raise_for_status()
        return _from_feed(url, res.text, limit=limit)
    except Exception as e:
        logger.warning(f"RSS fetch failed for {url}: {e}")
        return []


async def _fetch_rss_bundle(client: httpx.AsyncClient, feeds: list[str], limit: int) -> list:
    tasks = [_fetch_single_rss(client, feed_url, limit) for feed_url in feeds]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    articles = []
    for result in results:
        if isinstance(result, list):
            articles.extend(result)
    return _dedupe_articles(articles)


async def _fetch_newsapi_tech(client: httpx.AsyncClient) -> list:
    if not settings.NEWSAPI_KEY:
        return []
    try:
        res = await client.get(
            "https://newsapi.org/v2/top-headlines",
            params={"category": "technology", "language": "en", "pageSize": 20, "apiKey": settings.NEWSAPI_KEY},
        )
        res.raise_for_status()
        data = res.json()
        if data.get("status") != "ok":
            logger.warning(f"NewsAPI tech non-ok status: {data.get('status')}")
            return []
        articles = []
        for a in data.get("articles", []):
            articles.append({
                "title": a.get("title", ""),
                "link": a.get("url", ""),
                "summary": (a.get("description") or "")[:300],
                "published": a.get("publishedAt", ""),
                "source": a.get("source", {}).get("name", ""),
                "image": a.get("urlToImage", ""),
            })
        return _dedupe_articles(articles)
    except Exception as e:
        logger.warning(f"NewsAPI tech failed: {e}")
        return []


async def _fetch_newsapi_hiring(client: httpx.AsyncClient) -> list:
    if not settings.NEWSAPI_KEY:
        return []
    try:
        res = await client.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": "tech hiring OR startup jobs OR layoffs OR software engineer hiring",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 20,
                "apiKey": settings.NEWSAPI_KEY,
            },
        )
        res.raise_for_status()
        data = res.json()
        if data.get("status") != "ok":
            logger.warning(f"NewsAPI hiring non-ok status: {data.get('status')}")
            return []
        articles = []
        for a in data.get("articles", []):
            articles.append({
                "title": a.get("title", ""),
                "link": a.get("url", ""),
                "summary": (a.get("description") or "")[:300],
                "published": a.get("publishedAt", ""),
                "source": a.get("source", {}).get("name", ""),
                "image": a.get("urlToImage", ""),
            })
        return _dedupe_articles(articles)
    except Exception as e:
        logger.warning(f"NewsAPI hiring failed: {e}")
        return []


@router.get("/tech")
async def get_tech_news():
    """Fetch latest tech news quickly with NewsAPI + concurrent RSS fallback + cache."""
    cached = _get_cached("tech")
    if cached is not None:
        return {"success": True, "count": len(cached), "articles": cached[:30], "cached": True}

    timeout = httpx.Timeout(connect=2.0, read=4.0, write=4.0, pool=2.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        rss_task = asyncio.create_task(_fetch_rss_bundle(client, TECH_RSS_FEEDS, limit=8))
        news_articles = await _fetch_newsapi_tech(client)

        if news_articles:
            if not rss_task.done():
                rss_task.cancel()
                with suppress(asyncio.CancelledError):
                    await rss_task
            articles = news_articles
        else:
            articles = await rss_task

    articles = _dedupe_articles(articles)[:30]
    _set_cached("tech", articles)
    return {"success": True, "count": len(articles), "articles": articles, "cached": False}


@router.get("/hiring")
async def get_hiring_news():
    """Fetch hiring news quickly with NewsAPI + concurrent RSS fallback + cache."""
    cached = _get_cached("hiring")
    if cached is not None:
        return {"success": True, "count": len(cached), "articles": cached[:30], "cached": True}

    timeout = httpx.Timeout(connect=2.0, read=4.0, write=4.0, pool=2.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        rss_task = asyncio.create_task(_fetch_rss_bundle(client, HIRING_RSS_FEEDS, limit=10))
        news_articles = await _fetch_newsapi_hiring(client)

        if news_articles:
            if not rss_task.done():
                rss_task.cancel()
                with suppress(asyncio.CancelledError):
                    await rss_task
            articles = news_articles
        else:
            articles = await rss_task

    articles = _dedupe_articles(articles)[:30]
    _set_cached("hiring", articles)
    return {"success": True, "count": len(articles), "articles": articles, "cached": False}
