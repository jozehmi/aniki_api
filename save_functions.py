# save_functions.py - Funciones para guardar datos en la base de datos
from database import FilterOption, SessionLocal, Category, Genre, Tag, Media, MediaGenre, MediaTag, Episode, Embed, Download, MediaStatus, get_db
from datetime import datetime
from dateutil import parser
from slugify import slugify
from sqlalchemy.orm import Session
import re

# Función para inicializar filtros
def save_filters(filters_data: dict, db: Session):
    """
    Guarda las opciones de filtros en la tabla filter_options.
    
    Args:
        filters_data (dict): Diccionario con los filtros y sus opciones.
        db (Session): Sesión de la base de datos.
    """
    try:
        for filter_type, filter_info in filters_data.items():
            is_multiple = filter_info.get("type") == "multiple"
            if "options" in filter_info:
                for value in filter_info["options"]:
                    try:
                        option = FilterOption(
                            filter_type=filter_type,
                            value=value,
                            is_multiple=is_multiple,
                            added_at=datetime.utcnow()
                        )
                        db.add(option)
                        db.commit()
                        print(f"Guardando filtro {filter_type}: {value}")
                    except IntegrityError:
                        db.rollback()
                        print(f"Filtro {filter_type}: {value} ya existe")
                    except Exception as e:
                        db.rollback()
                        print(f"Error al guardar filtro {filter_type}: {value}: {e}")
            else:
                print(f"Filtro {filter_type} no tiene opciones para guardar")
        print("Todos los filtros procesados y guardados correctamente.")
    except Exception as e:
        db.rollback()
        print(f"Error general al guardar filtros: {e}")

# Función para guardar Anime Home
def save_anime_home(data: dict):
    db = next(get_db())
    status_map = {
        0: MediaStatus.PROXIMAMENTE,
        1: MediaStatus.FINALIZADO,
        2: MediaStatus.EMISION
    }
    try:
        print("Procesando featured...")
        for item in data.get("featured", []):
            try:
                print(f"Procesando media {item['id']}: {item['title']}")
                cat_data = item.get("category")
                if cat_data:
                    category = db.query(Category).filter(Category.id == cat_data["id"]).first()
                    if not category:
                        print(f"Creando categoría {cat_data['id']}: {cat_data['name']}")
                        category = Category(
                            id=cat_data["id"],
                            name=cat_data["name"],
                            slug=cat_data.get("slug", slugify(cat_data["name"])),  # Generar slug si no se proporciona
                            added_at=datetime.utcnow()
                        )
                        db.add(category)
                        db.commit()

                start_date = datetime.strptime(item["startDate"], "%Y-%m-%d").date() if item.get("startDate") else None
                media = db.query(Media).filter(Media.id == item["id"]).first()
                if not media:
                    print(f"Creando media {item['id']}: {item['title']}")
                    media = Media(
                        id=item["id"],
                        slug=item["slug"],
                        title=item["title"],
                        synopsis=item["synopsis"],
                        start_date=start_date,
                        status=status_map.get(item["status"]) if item.get("status") is not None else None,
                        image_url=item["image_url"],
                        watch_url=item["watch_url"],
                        type="anime",
                        category_id=cat_data["id"] if cat_data else None,
                        added_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()

                for g in item.get("genres", []):
                    genre = db.query(Genre).filter(Genre.id == g["id"]).first()
                    if not genre:
                        print(f"Creando género {g['id']}: {g['name']}")
                        genre = Genre(
                            id=g["id"],
                            name=g["name"],
                            slug=g["slug"],
                            added_at=datetime.utcnow()
                        )
                        db.add(genre)
                        db.commit()
                    assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
                    if not assoc:
                        print(f"Asociando género {g['id']} con media {media.id}")
                        assoc = MediaGenre(
                            media_id=media.id,
                            genre_id=genre.id,
                            added_at=datetime.utcnow()
                        )
                        db.add(assoc)
                        db.commit()
            except Exception as e:
                print(f"Error procesando featured item {item['id']}: {e}")
                db.rollback()
                continue

        print("Procesando latestEpisodes...")
        for ep in data.get("latestEpisodes", []):
            try:
                print(f"Procesando episodio {ep['id']}")
                media_data = ep.get("media")
                media = db.query(Media).filter(Media.id == media_data["id"]).first()
                if not media:
                    print(f"Creando media {media_data['id']}: {media_data['title']}")
                    media = Media(
                        id=media_data["id"],
                        slug=media_data["slug"],
                        title=media_data["title"],
                        type="anime",
                        added_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()

                created_at = parser.isoparse(ep["createdAt"])
                episode = db.query(Episode).filter(Episode.id == ep["id"]).first()
                if not episode:
                    print(f"Creando episodio {ep['id']} para media {media.id}")
                    episode = Episode(
                        id=ep["id"],
                        media_id=media.id,
                        number=ep["number"],
                        created_at=created_at,
                        image_url=ep["image_url"],
                        watch_url=ep["watch_url"],
                        added_at=datetime.utcnow()
                    )
                    db.add(episode)
                    db.commit()
            except Exception as e:
                print(f"Error procesando episodio {ep['id']}: {e}")
                db.rollback()
                continue

        print("Procesando latestMedia...")
        for item in data.get("latestMedia", []):
            try:
                print(f"Procesando media {item['id']}: {item['title']}")
                cat_data = item.get("category")
                if cat_data:
                    category = db.query(Category).filter(Category.id == cat_data["id"]).first()
                    if not category:
                        print(f"Creando categoría {cat_data['id']}: {cat_data['name']}")
                        category = Category(
                            id=cat_data["id"],
                            name=cat_data["name"],
                            slug=cat_data.get("slug", slugify(cat_data["name"])),  # Generar slug si no se proporciona
                            added_at=datetime.utcnow()
                        )
                        db.add(category)
                        db.commit()

                created_at = parser.isoparse(item["createdAt"])
                media = db.query(Media).filter(Media.id == item["id"]).first()
                if not media:
                    print(f"Creando media {item['id']}: {item['title']}")
                    media = Media(
                        id=item["id"],
                        slug=item["slug"],
                        title=item["title"],
                        synopsis=item["synopsis"],
                        image_url=item["image_url"],
                        watch_url=item["watch_url"],
                        created_at=created_at,
                        poster=item["poster"],
                        type="anime",
                        category_id=cat_data["id"] if cat_data else None,
                        added_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()
            except Exception as e:
                print(f"Error procesando latestMedia item {item['id']}: {e}")
                db.rollback()
                continue

        db.commit()
        print("Todos los datos procesados y guardados correctamente.")
    except Exception as e:
        db.rollback()
        print(f"Error general en save_anime_home: {e}")
        raise
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
    status_map = {
        1: "emision",
        2: "finalizado",
        3: "proximamente"
    }
    db = next(get_db())
    try:
        cat_data = data.get("category")
        if cat_data:
            category = db.query(Category).filter(Category.id == cat_data["id"]).first()
            if not category:
                category = Category(id=cat_data["id"], name=cat_data["name"], slug=cat_data.get("slug"))
                db.add(category)

        start_date = datetime.strptime(data["startDate"], "%Y-%m-%d").date() if data.get("startDate") else None
        end_date = datetime.strptime(data["endDate"], "%Y-%m-%d").date() if data.get("endDate") else None
        next_date = datetime.strptime(data["nextDate"], "%Y-%m-%d").date() if data.get("nextDate") else None
        created_at = datetime.fromisoformat(data["createdAt"].replace("+00", "Z"))
        updated_at = datetime.fromisoformat(data["updatedAt"].replace("+00", "Z"))

        status_val = data.get("status")
        status_str = None
        if status_val is not None:
            if isinstance(status_val, int):
                status_str = status_map.get(status_val)
            elif isinstance(status_val, str):
                status_str = status_val
        status_enum = MediaStatus(status_str) if status_str else None

        media = db.query(Media).filter(Media.id == data["id"]).first()
        if not media:
            media = Media(
                id=data["id"], slug=data["slug"], title=data["title"], aka=data.get("aka"), synopsis=data.get("synopsis"),
                start_date=start_date, end_date=end_date, next_date=next_date, wait_days=data.get("waitDays"),
                status=status_enum, runtime=data.get("runtime"), featured=data.get("featured"), mature=data.get("mature"),
                episodes_count=data.get("episodesCount"), score=data.get("score"), votes=data.get("votes"),
                mal_id=data.get("malId"), seasons=data.get("seasons"), backdrop=data.get("backdrop"),
                trailer=data.get("trailer"), poster=data.get("poster"), created_at=created_at, updated_at=updated_at,
                type="anime", category_id=data.get("categoryId")
            )
            db.add(media)
        else:
            media.aka = data.get("aka", media.aka)
            media.synopsis = data.get("synopsis", media.synopsis)
            media.start_date = start_date or media.start_date
            media.end_date = end_date or media.end_date
            media.next_date = next_date or media.next_date
            media.wait_days = data.get("waitDays", media.wait_days)
            media.status = status_enum or media.status
            media.runtime = data.get("runtime", media.runtime)
            media.featured = data.get("featured", media.featured)
            media.mature = data.get("mature", media.mature)
            media.episodes_count = data.get("episodesCount", media.episodes_count)
            media.score = data.get("score", media.score)
            media.votes = data.get("votes", media.votes)
            media.mal_id = data.get("malId", media.mal_id)
            media.seasons = data.get("seasons", media.seasons)
            media.backdrop = data.get("backdrop", media.backdrop)
            media.trailer = data.get("trailer", media.trailer)
            media.poster = data.get("poster", media.poster)
            media.created_at = created_at or media.created_at
            media.updated_at = updated_at or media.updated_at

        # Procesar géneros
        for g in data.get("genres", []):
            genre = db.query(Genre).filter(Genre.id == g["id"]).first()
            if not genre:
                genre = Genre(id=g["id"], name=g["name"], slug=g["slug"])
                db.add(genre)
            assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
            if not assoc:
                assoc = MediaGenre(media_id=media.id, genre_id=genre.id)
                db.add(assoc)

        # Procesar tags
        for tag_id in data.get("tags", []):
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                tag = Tag(id=tag_id)
                db.add(tag)
            assoc = db.query(MediaTag).filter(MediaTag.media_id == media.id, MediaTag.tag_id == tag.id).first()
            if not assoc:
                assoc = MediaTag(media_id=media.id, tag_id=tag.id)
                db.add(assoc)

        # Procesar episodios
        # In save_functions.py, update the episode processing loop in save_anime_details
        # Procesar episodios
        for ep in data.get("episodes", []):
            ep_id = ep.get("id")  # Use real ID if available
            if ep_id:
                episode = db.query(Episode).filter(Episode.id == ep_id).first()
            else:
                episode = db.query(Episode).filter(Episode.media_id == media.id, Episode.number == ep["number"]).first()
            if not episode:
                episode = Episode(
                    id=ep_id,  # Set ID if present
                    media_id=media.id,
                    number=ep["number"],
                    image_url=ep.get("image"),
                    watch_url=ep.get("url"),
                    added_at=datetime.utcnow()
                )
                db.add(episode)
            else:
                # Update if exists
                episode.image_url = ep.get("image") or episode.image_url
                episode.watch_url = ep.get("url") or episode.watch_url
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()


# Función para guardar Anime Episode
# Función para guardar Anime Episode
def save_anime_episode(data: dict):
    status_map = {
        1: "emision",
        2: "finalizado",
        3: "proximamente"
    }
    db = next(get_db())
    try:
        anime_data = data.get("anime")
        status_val = anime_data.get("status")
        status_str = None
        if status_val is not None:
            if isinstance(status_val, int):
                status_str = status_map.get(status_val)
            elif isinstance(status_val, str):
                status_str = status_val
        status_enum = MediaStatus(status_str) if status_str else None

        media = db.query(Media).filter(Media.id == anime_data["id"]).first()
        if not media:
            media = Media(
                id=anime_data["id"], title=anime_data["title"], aka=anime_data.get("aka"),
                score=anime_data.get("score"), votes=anime_data.get("votes"), mal_id=anime_data.get("malId"),
                status=status_enum, episodes_count=anime_data.get("episodes_count"), type="anime"
            )
            db.add(media)
        else:
            media.score = anime_data.get("score", media.score)
            media.votes = anime_data.get("votes", media.votes)
            media.mal_id = anime_data.get("malId", media.mal_id)
            media.status = status_enum or media.status
            media.episodes_count = anime_data.get("episodes_count", media.episodes_count)

        for genre_name in anime_data.get("genres", []):
            genre = db.query(Genre).filter(Genre.name == genre_name).first()
            if genre:
                assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
                if not assoc:
                    assoc = MediaGenre(media_id=media.id, genre_id=genre.id)
                    db.add(assoc)

        ep_data = data.get("episode")

        # Modificación: Lógica para manejar placeholders y evitar duplicados
        episode = db.query(Episode).filter(Episode.id == ep_data["id"]).first()
        if not episode:
            episode_by_key = db.query(Episode).filter(Episode.media_id == media.id, Episode.number == ep_data["number"]).first()
            image_url = None
            watch_url = None
            if episode_by_key:
                if episode_by_key.id < 100000:  # Umbral para detectar placeholders (ajusta si es necesario)
                    image_url = episode_by_key.image_url
                    watch_url = episode_by_key.watch_url
                    db.delete(episode_by_key)
                    db.commit()
            episode = Episode(
                id=ep_data["id"],
                media_id=media.id,
                number=ep_data["number"],
                filler=ep_data["filler"],
                image_url=image_url,
                watch_url=watch_url,
                added_at=datetime.utcnow()
            )
            db.add(episode)
        else:
            # Si ya existe por ID real, actualiza campos si es necesario
            episode.filler = ep_data["filler"]

        for emb in data.get("embeds", []):
            embed = db.query(Embed).filter(Embed.episode_id == episode.id, Embed.server == emb["server"], Embed.url == emb["url"]).first()
            if not embed:
                embed = Embed(episode_id=episode.id, server=emb["server"], url=emb["url"], variant=emb["variant"])
                db.add(embed)

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