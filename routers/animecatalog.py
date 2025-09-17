from fastapi import APIRouter, Query, HTTPException
from bs4 import BeautifulSoup
import re, requests
from core.cache import get_cached, set_cache
from core.config import BASE_URL, VALID_CATEGORIES, VALID_GENRES, VALID_STATUS, VALID_ORDERS, VALID_LETTERS
from save_anime_functions import save_anime_catalog

router = APIRouter()

# -------------------- /animes --------------------
@router.get("")
def get_animes(
    search: str = None,                # <-- Añadido
    category: list[str] = Query(None),
    genre: list[str] = Query(None),
    min_year: int = None,
    max_year: int = None,
    status: str = None,
    order: str = "predeterminado",
    letter: str = None,
    page: int = 1
):
    if category and not all(c in VALID_CATEGORIES for c in category):
        raise HTTPException(status_code=400, detail=f"Category inválida. Opciones: {VALID_CATEGORIES}")
    if genre and not all(g in VALID_GENRES for g in genre):
        raise HTTPException(status_code=400, detail=f"Genre inválido. Opciones: {VALID_GENRES}")
    if status and status not in VALID_STATUS:
        raise HTTPException(status_code=400, detail=f"Status inválido. Opciones: {VALID_STATUS}")
    if order and order not in VALID_ORDERS:
        raise HTTPException(status_code=400, detail=f"Order inválido. Opciones: {VALID_ORDERS}")
    if letter and letter.upper() not in VALID_LETTERS:
        raise HTTPException(status_code=400, detail=f"Letter inválida. Opciones: {VALID_LETTERS}")
    if min_year and max_year and min_year > max_year:
        raise HTTPException(status_code=400, detail="min_year no puede ser mayor que max_year")
    base_url = f"{BASE_URL}/catalogo"
    params = []
    if search:                        # <-- Añadido
        params.append(f"search={search}")
    if category:
        for cat in category:
            params.append(f"category={cat}")
    if genre:
        for g in genre:
            params.append(f"genre={g}")
    if min_year:
        params.append(f"minYear={min_year}")
    if max_year:
        params.append(f"maxYear={max_year}")
    if status:
        params.append(f"status={status}")
    if order:
        params.append(f"order={order}")
    if letter:
        params.append(f"letter={letter.upper()}")
    params.append(f"page={page}")
    url = base_url + "?" + "&".join(params) if params else base_url
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Failed to fetch the page", "url": url}
    soup = BeautifulSoup(response.text, "html.parser")
    scripts = soup.find_all("script")
    data_script = None
    for script in scripts:
        if script.string and "__sveltekit_" in script.string:
            data_script = script.string
            break
    if not data_script:
        return {"error": "Data script not found", "url": url}
    results_match = re.search(r"results:\s*\[([\s\S]*?)\]\s*}", data_script)
    if not results_match:
        return {"error": "Results not found in script", "url": url}
    results_str = results_match.group(1)
    anime_strs = re.split(r"\}\s*,\s*\{", results_str)
    animes = []
    for i, anime_str in enumerate(anime_strs):
        if i > 0:
            anime_str = "{" + anime_str
        if i < len(anime_strs) - 1:
            anime_str += "}"
        id_match = re.search(r'id:"([^"]+)"', anime_str)
        title_match = re.search(r'title:"([^"]+)"', anime_str)
        synopsis_match = re.search(r'synopsis:"(.*?)"(?=\s*,\s*categoryId:)', anime_str, re.DOTALL)
        category_id_match = re.search(r'categoryId:(\d+)', anime_str)
        slug_match = re.search(r'slug:"([^"]+)"', anime_str)
        anime_dict = {}
        if id_match:
            anime_id = id_match.group(1)
            anime_dict["id"] = anime_id
            anime_dict["cover"] = f"https://cdn.animeav1.com/covers/{anime_id}.jpg"
        if title_match:
            anime_dict["title"] = title_match.group(1)
        if synopsis_match:
            anime_dict["synopsis"] = synopsis_match.group(1).replace("\n", "\n")
        if category_id_match:
            anime_dict["categoryId"] = int(category_id_match.group(1))
        if slug_match:
            anime_dict["slug"] = slug_match.group(1)
        # Fix category slug to use the correct slug from input or VALID_CATEGORIES
        category_match = re.search(r'a\.name="([^"]+)"', data_script)
        category_name = category_match.group(1) if category_match else "Unknown"
        category_slug = "tv-anime"  # Default
        if category and len(category) == 1:
            category_slug = category[0]
        elif anime_dict.get("categoryId"):
            category_map = {
                1: "tv-anime",
                2: "pelicula",
                3: "ova",
                4: "especial"
            }
            category_slug = category_map.get(anime_dict["categoryId"], "tv-anime")
        anime_dict["category"] = {
            "id": anime_dict.get("categoryId"),
            "name": category_name,
            "slug": category_slug
        }
        if anime_dict:
            animes.append(anime_dict)
    total_results = len(animes)
    results_elem = soup.find(string=re.compile(r"\d+ Resultados"))
    if results_elem:
        match = re.search(r"\d+", results_elem)
        if match:
            total_results = int(match.group())
    total_pages = 1
    pagination_links = soup.find_all("a", href=lambda href: href and "page=" in href if href else False)
    pages = [int(plink.text) for plink in pagination_links if plink.text.isdigit()]
    if pages:
        total_pages = max(pages)
    result = {
        "url": url,
        "page": page,
        "total_results": total_results,
        "total_pages": total_pages,
        "animes": animes,
    }
    save_anime_catalog(result)
    return result
