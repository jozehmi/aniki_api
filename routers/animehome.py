from fastapi import APIRouter, Query
from bs4 import BeautifulSoup
import re, demjson3
from utils.scraping import fetch_html, find_sveltekit_script, extract_home_block
from utils.builders import (
    build_featured_image_url, build_latest_episode_image_url,
    build_latest_media_image_url, build_watch_url
)
from core.cache import get_cached, set_cache
from core.config import BASE_URL
from save_anime_functions import save_anime_home

router = APIRouter()

def validate_home_data(data):
    required_keys = ["featured", "latestEpisodes", "latestMedia"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Falta la clave '{key}' en los datos de entrada")
    for item in data["featured"]:
        if not all(k in item for k in ["id", "slug", "title", "synopsis", "image_url", "watch_url"]):
            raise ValueError(f"Elemento en 'featured' incompleto: {item}")
        if item.get("startDate") and not re.match(r"\d{4}-\d{2}-\d{2}", item["startDate"]):
            raise ValueError(f"Formato de startDate inválido en: {item}")
        if item.get("status") is not None and item["status"] not in [0, 1, 2]:
            raise ValueError(f"Valor de status inválido en: {item}")
    for ep in data["latestEpisodes"]:
        if not all(k in ep for k in ["id", "media", "number", "createdAt", "image_url", "watch_url"]):
            raise ValueError(f"Elemento en 'latestEpisodes' incompleto: {ep}")
        if not re.match(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(\.\d+)?(\+\d{2}(:\d{2})?)?", ep["createdAt"]):
            raise ValueError(f"Formato de createdAt inválido en: {ep}")
    for item in data["latestMedia"]:
        if not all(k in item for k in ["id", "slug", "title", "synopsis", "createdAt", "image_url", "watch_url"]):
            raise ValueError(f"Elemento en 'latestMedia' incompleto: {item}")
        if not re.match(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(\.\d+)?(\+\d{2}(:\d{2})?)?", item["createdAt"]):
            raise ValueError(f"Formato de createdAt inválido en: {item}")
    return True

@router.get("/home")
async def get_home_data(force_refresh: bool = Query(False)):
    if not force_refresh:
        cached = get_cached("home_data")
        if cached:
            return cached

    html = await fetch_html(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")
    script_tag = find_sveltekit_script(soup)
    result = {"featured": [], "latestEpisodes": [], "latestMedia": []}

    if script_tag:
        try:
            home_js = extract_home_block(script_tag)
            home_data = demjson3.decode(home_js)

            # Featured
            for item in home_data.get("featured", []):
                anime_id = item.get("id")
                slug = item.get("slug")
                item["image_url"] = build_featured_image_url(anime_id)
                item["watch_url"] = build_watch_url(slug)
                result["featured"].append(item)

            # Latest Episodes
            for ep in home_data.get("latestEpisodes", []):
                media = ep.get("media", {})
                anime_id = media.get("id")
                slug = media.get("slug")
                ep["image_url"] = build_latest_episode_image_url(anime_id)
                ep["watch_url"] = build_watch_url(slug)
                result["latestEpisodes"].append(ep)

            # Latest Media
            for item in home_data.get("latestMedia", []):
                anime_id = item.get("id")
                slug = item.get("slug")
                item["image_url"] = build_latest_media_image_url(anime_id)
                item["watch_url"] = build_watch_url(slug)
                result["latestMedia"].append(item)

            # Validar y guardar los datos
            try:
                validate_home_data(result)
                save_anime_home(result)
            except Exception as e:
                print(f"Error al guardar en la base de datos: {e}, datos problemáticos: {result}")
                raise

            set_cache("home_data", result)
            return result
        except Exception as e:
            print(f"[WARN] Fallback a scraping: {e}")

    set_cache("home_data", result)
    return result
