from fastapi import APIRouter, Query, HTTPException
from bs4 import BeautifulSoup
import re, json
from utils.scraping import fetch_html, find_sveltekit_script
from core.cache import get_cached, set_cache
from core.config import BASE_URL
from save_anime_functions import save_anime_episode

router = APIRouter()

# -------------------- /{slug}/{number} --------------------
@router.get("/{slug}/{number}")
async def get_episode(slug: str, number: int, force_refresh: bool = Query(False)):
    cache_key = f"{slug}_ep_{number}"
    if not force_refresh:
        cached = get_cached(cache_key)
        if cached:
            return cached
    url = f"{BASE_URL}/media/{slug}/{number}"
    html = await fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    script_text = find_sveltekit_script(soup)
    if not script_text:
        raise HTTPException(status_code=500, detail="No se encontró bloque de datos")
    try:
        m = re.search(r"data\s*:\s*\[", script_text)
        if not m:
            raise HTTPException(status_code=500, detail="No se encontró 'data:[' en el script")
        start = script_text.find("[", m.start())
        depth, end = 0, None
        for i in range(start, len(script_text)):
            ch = script_text[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end is None:
            raise HTTPException(status_code=500, detail="No se cerró el array de 'data'")
        data_js = script_text[start:end + 1]
        data_json = re.sub(r'([{\[,]\s*)([A-Za-z0-9_@$-]+)\s*:', r'\1"\2":', data_js)
        data_json = data_json.replace("undefined", "null").replace("void 0", "null")
        data_json = re.sub(r',\s*(\]|})', r'\1', data_json)
        data = json.loads(data_json)
        media_block = None
        ep_block = None
        for item in data:
            if isinstance(item, dict) and item.get("type") == "data":
                dd = item.get("data", {})
                if media_block is None and "media" in dd:
                    media_block = dd["media"]
                if ep_block is None and "episode" in dd:
                    ep_block = dd
        if not media_block or not ep_block:
            raise HTTPException(status_code=500, detail="No se encontraron bloques 'media' o 'episode'")

        media = media_block
        episode = ep_block["episode"]

        def collect_servers(section: dict) -> list:
            out = []
            if not isinstance(section, dict):
                return out
            for variant, items in section.items():
                if isinstance(items, list):
                    for it in items:
                        out.append({
                            "server": it.get("server"),
                            "url": it.get("url"),
                            "variant": variant
                        })
            return out

        embeds = collect_servers(ep_block.get("embeds", {}))
        downloads = collect_servers(ep_block.get("downloads", {}))

        result = {
            "anime": {
                "id": media.get("id"),
                "title": media.get("title"),
                "aka": media.get("aka"),
                "genres": [g.get("name") for g in media.get("genres", []) if isinstance(g, dict)],
                "score": media.get("score"),
                "votes": media.get("votes"),
                "malId": media.get("malId"),
                "status": media.get("status"),
                "episodes_count": media.get("episodesCount"),
            },
            "episode": {
                "id": episode.get("id"),
                "number": episode.get("number"),
                "filler": episode.get("filler"),
            },
            "embeds": embeds,
            "downloads": downloads,
        }

        # Guardar los datos en la base
        try:
            save_anime_episode(result)
        except Exception as e:
            print(f"Error al guardar episodio en BD: {e}")

        set_cache(cache_key, result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al parsear episodio: {e}")
