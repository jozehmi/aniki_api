from fastapi import APIRouter, Query
from bs4 import BeautifulSoup
import re, demjson3
from utils.scraping import fetch_html, find_sveltekit_script, extract_js_object
from utils.builders import (
    build_poster_url, build_backdrop_url,
    build_episode_image_url, build_episode_url
)
from core.cache import get_cached, set_cache
from core.config import BASE_URL
from save_anime_functions import save_anime_details

router = APIRouter()

# -------------------- /{slug} --------------------
@router.get("/{slug}")
async def get_anime_details(slug: str, force_refresh: bool = Query(False)):
    if not force_refresh:
        cached = get_cached(slug)
        if cached:
            return cached

    # Fetch and parse details as before
    html = await fetch_html(f"{BASE_URL}/media/{slug}")
    soup = BeautifulSoup(html, "html.parser")
    script_tag = find_sveltekit_script(soup)
    if not script_tag:
        return {"error": "No se encontró el bloque de datos JSON"}

    try:
        media_js = extract_js_object(script_tag, "media:")
        media_data = demjson3.decode(media_js)
    except Exception as e:
        return {"error": f"Fallo al extraer/parsear media: {str(e)}"}

    anime_id = media_data.get("id")

    # Existing episode processing (placeholders without ID)
    episodes = []
    for ep in media_data.get("episodes", []):
        num = ep.get("number")
        if num is not None:
            episodes.append({
                "id": ep.get("id"),  # Include the real ID if present
                "number": num,
                "image": build_episode_image_url(anime_id, num),
                "url": build_episode_url(slug, num)
            })
        media_data.update({
            "poster": build_poster_url(anime_id),
            "backdrop": build_backdrop_url(anime_id),
            "episodes": episodes
        })

    # Check if episodes lack IDs (common case)
    if episodes and all("id" not in ep for ep in media_data.get("episodes", [])):
        # Asynchronously fetch one episode (e.g., #1) to get full IDs
        async def fetch_episode_ids():
            ep_html = await fetch_html(f"{BASE_URL}/media/{slug}/1")
            ep_soup = BeautifulSoup(ep_html, "html.parser")
            ep_script_text = find_sveltekit_script(ep_soup)
            if not ep_script_text:
                return None  # Fallback if fail
            try:
                # Parse like in get_episode
                m = re.search(r"data\s*:\s*\[", ep_script_text)
                if not m:
                    return None
                start = ep_script_text.find("[", m.start())
                depth, end = 0, None
                for i in range(start, len(ep_script_text)):
                    ch = ep_script_text[i]
                    if ch == "[":
                        depth += 1
                    elif ch == "]":
                        depth -= 1
                        if depth == 0:
                            end = i
                            break
                if end is None:
                    return None
                data_js = ep_script_text[start:end + 1]
                data_json = re.sub(r'([{\[,]\s*)([A-Za-z0-9_@$-]+)\s*:', r'\1"\2":', data_js)
                data_json = data_json.replace("undefined", "null").replace("void 0", "null")
                data_json = re.sub(r',\s*(\]|})', r'\1', data_json)
                data = json.loads(data_json)
                media_block = None
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "data":
                        dd = item.get("data", {})
                        if "media" in dd:
                            media_block = dd["media"]
                            break
                if media_block:
                    return media_block.get("episodes", [])
                return None
            except Exception:
                return None

        full_episodes = await fetch_episode_ids()
        if full_episodes:
            # Map IDs to the existing episodes list (assume ordered by number)
            id_map = {ep.get("number"): ep.get("id") for ep in full_episodes if ep.get("number") and ep.get("id")}
            for ep in episodes:
                num = ep.get("number")
                if num in id_map:
                    ep["id"] = id_map[num]

    media_data.update({
        "poster": build_poster_url(anime_id),
        "backdrop": build_backdrop_url(anime_id),
        "episodes": episodes
    })

    # Save with enriched data (now has IDs)
    try:
        save_anime_details(media_data)
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")

    set_cache(slug, media_data)
    return media_data
