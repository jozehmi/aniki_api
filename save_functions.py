# save_functions.py - Funciones para guardar datos en la base de datos
from database import FilterOption, SessionLocal, Category, Genre, Tag, Media, MediaGenre, MediaTag, Episode, Embed, Download, MediaStatus, get_db
from datetime import datetime
from sqlalchemy.orm import Session
import re

# Función para inicializar filtros
def initialize_filters():
    db = next(get_db())
    try:
        # Cargar categorías
        categories = [
            {"name": "TV Anime", "slug": "tv-anime"},
            {"name": "Pelicula", "slug": "pelicula"},
            {"name": "OVA", "slug": "ova"},
            {"name": "Especial", "slug": "especial"}
        ]
        for cat in categories:
            if not db.query(Category).filter(Category.slug == cat["slug"]).first():
                db.add(Category(**cat))
        db.commit()

        # Cargar géneros
        genres = [
            {"name": "Acción", "slug": "accion"},
            {"name": "Aventura", "slug": "aventura"},
            {"name": "Ciencia ficción", "slug": "ciencia-ficcion"},
            {"name": "Comedia", "slug": "comedia"},
            {"name": "Deportes", "slug": "deportes"},
            {"name": "Drama", "slug": "drama"},
            {"name": "Fantasía", "slug": "fantasia"},
            {"name": "Misterio", "slug": "misterio"},
            {"name": "Recuentos de la vida", "slug": "recuentos-de-la-vida"},
            {"name": "Romance", "slug": "romance"},
            {"name": "Seinen", "slug": "seinen"},
            {"name": "Shoujo", "slug": "shoujo"},
            {"name": "Shounen", "slug": "shounen"},
            {"name": "Sobrenatural", "slug": "sobrenatural"},
            {"name": "Suspenso", "slug": "suspenso"},
            {"name": "Terror", "slug": "terror"}
        ]
        for g in genres:
            if not db.query(Genre).filter(Genre.slug == g["slug"]).first():
                db.add(Genre(**g))
        db.commit()

        # Cargar opciones de filtros (opcional)
        filter_data = [
            {"filter_type": "Category", "value": "tv-anime", "is_multiple": True},
            {"filter_type": "Category", "value": "pelicula", "is_multiple": True},
            {"filter_type": "Category", "value": "ova", "is_multiple": True},
            {"filter_type": "Category", "value": "especial", "is_multiple": True},
            *[{"filter_type": "Genre", "value": g["slug"], "is_multiple": True} for g in genres],
            {"filter_type": "Status", "value": "emision", "is_multiple": False},
            {"filter_type": "Status", "value": "finalizado", "is_multiple": False},
            {"filter_type": "Status", "value": "proximamente", "is_multiple": False},
            {"filter_type": "Order", "value": "predeterminado", "is_multiple": False},
            {"filter_type": "Order", "value": "popular", "is_multiple": False},
            {"filter_type": "Order", "value": "score", "is_multiple": False},
            {"filter_type": "Order", "value": "title", "is_multiple": False},
            {"filter_type": "Order", "value": "latest_added", "is_multiple": False},
            {"filter_type": "Order", "value": "latest_released", "is_multiple": False},
            *[{"filter_type": "Letter", "value": l, "is_multiple": False} for l in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        ]
        for f in filter_data:
            if not db.query(FilterOption).filter(FilterOption.filter_type == f["filter_type"], FilterOption.value == f["value"]).first():
                db.add(FilterOption(**f))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

# Función para guardar Anime Home
def save_anime_home(data: dict):
    db = next(get_db())
    try:
        for item in data.get("featured", []):
            cat_data = item.get("category")
            if cat_data:
                category = db.query(Category).filter(Category.id == cat_data["id"]).first()
                if not category:
                    category = Category(id=cat_data["id"], name=cat_data["name"], slug=cat_data.get("slug", str(cat_data["id"])))
                    db.add(category)
                    db.commit()

            start_date = datetime.strptime(item["startDate"], "%Y-%m-%d").date() if item.get("startDate") else None
            media = db.query(Media).filter(Media.id == item["id"]).first()
            if not media:
                media = Media(
                    id=item["id"], slug=item["slug"], title=item["title"], synopsis=item["synopsis"],
                    start_date=start_date, status=MediaStatus(item["status"]) if item.get("status") else None,
                    image_url=item["image_url"], watch_url=item["watch_url"], type="anime",
                    category_id=cat_data["id"] if cat_data else None
                )
                db.add(media)
                db.commit()

            for g in item.get("genres", []):
                genre = db.query(Genre).filter(Genre.id == g["id"]).first()
                if not genre:
                    genre = Genre(id=g["id"], name=g["name"], slug=g["slug"])
                    db.add(genre)
                    db.commit()
                assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
                if not assoc:
                    assoc = MediaGenre(media_id=media.id, genre_id=genre.id)
                    db.add(assoc)
                    db.commit()

        for ep in data.get("latestEpisodes", []):
            media_data = ep.get("media")
            media = db.query(Media).filter(Media.id == media_data["id"]).first()
            if not media:
                media = Media(id=media_data["id"], slug=media_data["slug"], title=media_data["title"], type="anime")
                db.add(media)
                db.commit()

            created_at = datetime.fromisoformat(ep["createdAt"].replace("+00", "Z"))
            episode = db.query(Episode).filter(Episode.id == ep["id"]).first()
            if not episode:
                episode = Episode(
                    id=ep["id"], media_id=media.id, number=ep["number"],
                    created_at=created_at, image_url=ep["image_url"], watch_url=ep["watch_url"]
                )
                db.add(episode)
                db.commit()

        for item in data.get("latestMedia", []):
            cat_data = item.get("category")
            if cat_data:
                category = db.query(Category).filter(Category.id == cat_data["id"]).first()
                if not category:
                    category = Category(id=cat_data["id"], name=cat_data["name"], slug=cat_data.get("slug"))
                    db.add(category)
                    db.commit()

            created_at = datetime.fromisoformat(item["createdAt"].replace("+00", "Z"))
            media = db.query(Media).filter(Media.id == item["id"]).first()
            if not media:
                media = Media(
                    id=item["id"], slug=item["slug"], title=item["title"], synopsis=item["synopsis"],
                    image_url=item["image_url"], watch_url=item["watch_url"], created_at=created_at,
                    poster=item["poster"], type="anime", category_id=cat_data["id"] if cat_data else None
                )
                db.add(media)
                db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

# Función para guardar Anime Catalog
def save_anime_catalog(data: dict):
    db = next(get_db())
    try:
        for anime in data.get("animes", []):
            cat_data = anime.get("category")
            if cat_data:
                category = db.query(Category).filter(Category.id == cat_data["id"]).first()
                if not category:
                    category = Category(id=cat_data["id"], name=cat_data["name"], slug=cat_data.get("slug"))
                    db.add(category)
                    db.commit()

            media = db.query(Media).filter(Media.id == anime["id"]).first()
            if not media:
                media = Media(
                    id=anime["id"], slug=anime["slug"], title=anime["title"], synopsis=anime["synopsis"],
                    image_url=anime["cover"], type="anime", category_id=anime["categoryId"]
                )
                db.add(media)
                db.commit()
            else:
                media.synopsis = anime["synopsis"] or media.synopsis
                media.image_url = anime["cover"] or media.image_url
                db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

# Función para guardar Anime Details
def save_anime_details(data: dict):
    db = next(get_db())
    try:
        cat_data = data.get("category")
        if cat_data:
            category = db.query(Category).filter(Category.id == cat_data["id"]).first()
            if not category:
                category = Category(id=cat_data["id"], name=cat_data["name"], slug=cat_data.get("slug"))
                db.add(category)
                db.commit()

        start_date = datetime.strptime(data["startDate"], "%Y-%m-%d").date() if data.get("startDate") else None
        end_date = datetime.strptime(data["endDate"], "%Y-%m-%d").date() if data.get("endDate") else None
        next_date = datetime.strptime(data["nextDate"], "%Y-%m-%d").date() if data.get("nextDate") else None
        created_at = datetime.fromisoformat(data["createdAt"].replace("+00", "Z"))
        updated_at = datetime.fromisoformat(data["updatedAt"].replace("+00", "Z"))
        media = db.query(Media).filter(Media.id == data["id"]).first()
        if not media:
            media = Media(
                id=data["id"], slug=data["slug"], title=data["title"], aka=data["aka"], synopsis=data["synopsis"],
                start_date=start_date, end_date=end_date, next_date=next_date, wait_days=data["waitDays"],
                status=MediaStatus(data["status"]) if data.get("status") else None, runtime=data["runtime"],
                featured=data["featured"], mature=data["mature"], episodes_count=data["episodesCount"],
                score=data["score"], votes=data["votes"], mal_id=data["malId"], seasons=data["seasons"],
                backdrop=data["backdrop"], trailer=data["trailer"], poster=data["poster"], created_at=created_at,
                updated_at=updated_at, type="anime", category_id=data["categoryId"]
            )
            db.add(media)
            db.commit()
        else:
            media.aka = data["aka"] or media.aka
            media.synopsis = data["synopsis"] or media.synopsis
            media.start_date = start_date or media.start_date
            media.end_date = end_date or media.end_date
            media.next_date = next_date or media.next_date
            media.wait_days = data["waitDays"] or media.wait_days
            media.status = MediaStatus(data["status"]) if data.get("status") else media.status
            media.runtime = data["runtime"] or media.runtime
            media.featured = data["featured"] or media.featured
            media.mature = data["mature"] or media.mature
            media.episodes_count = data["episodesCount"] or media.episodes_count
            media.score = data["score"] or media.score
            media.votes = data["votes"] or media.votes
            media.mal_id = data["malId"] or media.mal_id
            media.seasons = data["seasons"] or media.seasons
            media.backdrop = data["backdrop"] or media.backdrop
            media.trailer = data["trailer"] or media.trailer
            media.poster = data["poster"] or media.poster
            media.created_at = created_at or media.created_at
            media.updated_at = updated_at or media.updated_at
            db.commit()

        for g in data.get("genres", []):
            genre = db.query(Genre).filter(Genre.id == g["id"]).first()
            if not genre:
                genre = Genre(id=g["id"], name=g["name"], slug=g["slug"])
                db.add(genre)
                db.commit()
            assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
            if not assoc:
                assoc = MediaGenre(media_id=media.id, genre_id=genre.id)
                db.add(assoc)
                db.commit()

        for tag_id in data.get("tags", []):
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                tag = Tag(id=tag_id)
                db.add(tag)
                db.commit()
            assoc = db.query(MediaTag).filter(MediaTag.media_id == media.id, MediaTag.tag_id == tag.id).first()
            if not assoc:
                assoc = MediaTag(media_id=media.id, tag_id=tag.id)
                db.add(assoc)
                db.commit()

        for ep in data.get("episodes", []):
            episode = db.query(Episode).filter(Episode.media_id == media.id, Episode.number == ep["number"]).first()
            if not episode:
                episode = Episode(media_id=media.id, number=ep["number"], image_url=ep["image"], watch_url=ep["url"])
                db.add(episode)
                db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

# Función para guardar Anime Episode
def save_anime_episode(data: dict):
    db = next(get_db())
    try:
        anime_data = data.get("anime")
        media = db.query(Media).filter(Media.id == anime_data["id"]).first()
        if not media:
            media = Media(
                id=anime_data["id"], title=anime_data["title"], aka=anime_data["aka"], score=anime_data["score"],
                votes=anime_data["votes"], mal_id=anime_data["malId"], status=MediaStatus(anime_data["status"]) if anime_data.get("status") else None,
                episodes_count=anime_data["episodes_count"], type="anime"
            )
            db.add(media)
            db.commit()
        else:
            media.score = anime_data["score"] or media.score
            media.votes = anime_data["votes"] or media.votes
            media.mal_id = anime_data["malId"] or media.mal_id
            media.status = MediaStatus(anime_data["status"]) if anime_data.get("status") else media.status
            media.episodes_count = anime_data["episodes_count"] or media.episodes_count
            db.commit()

        for genre_name in anime_data.get("genres", []):
            genre = db.query(Genre).filter(Genre.name == genre_name).first()
            if genre:
                assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
                if not assoc:
                    assoc = MediaGenre(media_id=media.id, genre_id=genre.id)
                    db.add(assoc)
                    db.commit()

        ep_data = data.get("episode")
        episode = db.query(Episode).filter(Episode.id == ep_data["id"]).first()
        if not episode:
            episode = Episode(id=ep_data["id"], media_id=media.id, number=ep_data["number"], filler=ep_data["filler"])
            db.add(episode)
            db.commit()
        else:
            episode.filler = ep_data["filler"]
            db.commit()

        for emb in data.get("embeds", []):
            embed = db.query(Embed).filter(Embed.episode_id == episode.id, Embed.server == emb["server"], Embed.url == emb["url"]).first()
            if not embed:
                embed = Embed(episode_id=episode.id, server=emb["server"], url=emb["url"], variant=emb["variant"])
                db.add(embed)
                db.commit()

        for dl in data.get("downloads", []):
            download = db.query(Download).filter(Download.episode_id == episode.id, Download.server == dl["server"], Download.url == dl["url"]).first()
            if not download:
                download = Download(episode_id=episode.id, server=dl["server"], url=dl["url"], variant=dl["variant"])
                db.add(download)
                db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

# Función auxiliar para generar un slug
def generate_slug(name: str) -> str:
    """Convierte un nombre en un slug (minúsculas, sin espacios, solo caracteres alfanuméricos y guiones)."""
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower()).replace(' ', '-')
    return slug or 'default-slug'  # Fallback si el nombre está vacío

# Función para guardar Anime Schedule
def save_anime_schedule(data: dict):
    db = next(get_db())
    try:
        for item in data.get("schedule", []):
            cat_data = item.get("category")
            if cat_data:
                category = db.query(Category).filter(Category.id == cat_data["id"]).first()
                if not category:
                    # Usar slug de cat_data si existe, o generar uno
                    slug = cat_data.get("slug") or generate_slug(cat_data["name"])
                    category = Category(id=cat_data["id"], name=cat_data["name"], slug=slug)
                    db.add(category)
                    db.commit()

            start_date = datetime.strptime(item["startDate"], "%Y-%m-%d").date() if item.get("startDate") else None
            created_at = datetime.fromisoformat(item["createdAt"].replace("+00", "Z"))
            media = db.query(Media).filter(Media.id == item["id"]).first()
            if not media:
                media = Media(
                    id=item["id"], slug=item["slug"], title=item["title"], synopsis=item["synopsis"],
                    start_date=start_date, poster=item["poster"], created_at=created_at, type="anime",
                    category_id=cat_data["id"] if cat_data else None, day=item["day"], time=item["time"]
                )
                db.add(media)
                db.commit()
            else:
                media.day = item["day"] or media.day
                media.time = item["time"] or media.time
                db.commit()

            le_data = item.get("latestEpisode")
            if le_data:
                created_at_ep = datetime.fromisoformat(le_data["createdAt"].replace("+00:00", ""))
                episode = db.query(Episode).filter(Episode.id == le_data["id"]).first()
                if not episode:
                    episode = Episode(id=le_data["id"], media_id=media.id, number=le_data["number"], created_at=created_at_ep)
                    db.add(episode)
                    db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error al guardar en la base de datos: {e}")
        raise  # Relanzar para depuración; quitar en producción si prefieres
    finally:
        db.close()