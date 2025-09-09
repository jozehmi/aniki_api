from sqlalchemy.exc import IntegrityError
from database import FilterOption, Genre, Media, ContentUnit, Embed, Download, MediaStatus, MediaType, get_db
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
            if "values" in filter_info:
                for value in filter_info["values"]:
                    try:
                        option = FilterOption(
                            filter_type=filter_type,
                            value=value,
                            description=filter_info.get("description"),
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
                print(f"Filtro {filter_type} no tiene valores para guardar")
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
                mt_data = item.get("category")
                if mt_data:
                    media_type = db.query(MediaType).filter(MediaType.name == mt_data["name"]).first()
                    if not media_type:
                        print(f"Creando media_type {mt_data['name']}")
                        media_type = MediaType(
                            name=mt_data["name"],
                            description=mt_data.get("description", f"Tipo {mt_data['name']}"),
                            added_at=datetime.utcnow()
                        )
                        db.add(media_type)
                        db.commit()

                start_date = parser.parse(item["startDate"]).date() if item.get("startDate") else None
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
                        image_url=item.get("image_url"),
                        watch_url=item.get("watch_url"),
                        media_type_id=media_type.id if mt_data else None,
                        featured=True,
                        created_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()

                for g in item.get("genres", []):
                    genre = db.query(Genre).filter(Genre.slug == g["slug"]).first()
                    if not genre:
                        print(f"Creando género {g['name']}: {g['slug']}")
                        genre = Genre(
                            name=g["name"],
                            slug=g["slug"],
                            added_at=datetime.utcnow()
                        )
                        db.add(genre)
                        db.commit()
                    assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
                    if not assoc:
                        print(f"Asociando género {g['slug']} con media {media.id}")
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
                    mt_name = media_data.get("category", {}).get("name", "tv-anime")
                    media_type = db.query(MediaType).filter(MediaType.name == mt_name).first()
                    if not media_type:
                        media_type = MediaType(
                            name=mt_name,
                            description=f"Tipo {mt_name}",
                            added_at=datetime.utcnow()
                        )
                        db.add(media_type)
                        db.commit()
                    print(f"Creando media {media_data['id']}: {media_data['title']}")
                    media = Media(
                        id=media_data["id"],
                        slug=media_data["slug"],
                        title=media_data["title"],
                        media_type_id=media_type.id,
                        created_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()

                created_at = parser.isoparse(ep["createdAt"]) if ep.get("createdAt") else datetime.utcnow()
                content_unit = db.query(ContentUnit).filter(ContentUnit.id == ep["id"]).first()
                if not content_unit:
                    print(f"Creando content_unit {ep['id']} para media {media.id}")
                    content_unit = ContentUnit(
                        id=ep["id"],
                        media_id=media.id,
                        type="episode",
                        number=ep["number"],
                        image_url=ep.get("image_url"),
                        url=ep.get("watch_url"),
                        published_at=created_at,
                        created_at=datetime.utcnow()
                    )
                    db.add(content_unit)
                    db.commit()
            except Exception as e:
                print(f"Error procesando episodio {ep['id']}: {e}")
                db.rollback()
                continue

        print("Procesando latestMedia...")
        for item in data.get("latestMedia", []):
            try:
                print(f"Procesando media {item['id']}: {item['title']}")
                mt_data = item.get("category")
                if mt_data:
                    media_type = db.query(MediaType).filter(MediaType.name == mt_data["name"]).first()
                    if not media_type:
                        print(f"Creando media_type {mt_data['name']}")
                        media_type = MediaType(
                            name=mt_data["name"],
                            description=mt_data.get("description", f"Tipo {mt_data['name']}"),
                            added_at=datetime.utcnow()
                        )
                        db.add(media_type)
                        db.commit()

                created_at = parser.isoparse(item["createdAt"]) if item.get("createdAt") else datetime.utcnow()
                media = db.query(Media).filter(Media.id == item["id"]).first()
                if not media:
                    print(f"Creando media {item['id']}: {item['title']}")
                    media = Media(
                        id=item["id"],
                        slug=item["slug"],
                        title=item["title"],
                        synopsis=item.get("synopsis"),
                        image_url=item.get("image_url"),
                        watch_url=item.get("watch_url"),
                        backdrop_url=item.get("poster"),
                        media_type_id=media_type.id if mt_data else None,
                        created_at=created_at
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
            mt_data = anime.get("category")
            if mt_data:
                media_type = db.query(MediaType).filter(MediaType.name == mt_data["name"]).first()
                if not media_type:
                    media_type = MediaType(
                        name=mt_data["name"],
                        description=mt_data.get("description", f"Tipo {mt_data['name']}"),
                        added_at=datetime.utcnow()
                    )
                    db.add(media_type)
                    db.commit()

            media = db.query(Media).filter(Media.id == anime["id"]).first()
            if not media:
                media = Media(
                    id=anime["id"],
                    slug=anime["slug"],
                    title=anime["title"],
                    synopsis=anime.get("synopsis"),
                    image_url=anime.get("cover"),
                    media_type_id=media_type.id if mt_data else None,
                    created_at=datetime.utcnow()
                )
                db.add(media)
                db.commit()
            else:
                media.synopsis = anime.get("synopsis") or media.synopsis
                media.image_url = anime.get("cover") or media.image_url
                db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

# Función para guardar Anime Details
def save_anime_details(data: dict):
    status_map = {
        1: MediaStatus.EMISION,
        2: MediaStatus.FINALIZADO,
        3: MediaStatus.PROXIMAMENTE
    }
    db = next(get_db())
    try:
        mt_data = data.get("category")
        if mt_data:
            media_type = db.query(MediaType).filter(MediaType.name == mt_data["name"]).first()
            if not media_type:
                media_type = MediaType(
                    name=mt_data["name"],
                    description=mt_data.get("description", f"Tipo {mt_data['name']}"),
                    added_at=datetime.utcnow()
                )
                db.add(media_type)
                db.commit()

        start_date = parser.parse(data["startDate"]).date() if data.get("startDate") else None
        end_date = parser.parse(data["endDate"]).date() if data.get("endDate") else None
        created_at = parser.isoparse(data["createdAt"].replace("+00", "Z")) if data.get("createdAt") else datetime.utcnow()
        updated_at = parser.isoparse(data["updatedAt"].replace("+00", "Z")) if data.get("updatedAt") else None

        status_val = data.get("status")
        status_enum = status_map.get(status_val) if isinstance(status_val, int) else MediaStatus(status_val) if status_val else None

        media = db.query(Media).filter(Media.id == data["id"]).first()
        if not media:
            media = Media(
                id=data["id"],
                slug=data["slug"],
                title=data["title"],
                alternative_titles=data.get("aka"),
                synopsis=data.get("synopsis"),
                start_date=start_date,
                end_date=end_date,
                status=status_enum,
                score=data.get("score"),
                votes=data.get("votes"),
                backdrop_url=data.get("backdrop"),
                trailer_url=data.get("trailer"),
                image_url=data.get("poster"),
                watch_url=data.get("watch_url"),
                seasons=data.get("seasons"),
                mature=data.get("mature", False),
                featured=data.get("featured", False),
                media_type_id=media_type.id if mt_data else None,
                created_at=created_at,
                updated_at=updated_at
            )
            db.add(media)
        else:
            media.alternative_titles = data.get("aka", media.alternative_titles)
            media.synopsis = data.get("synopsis", media.synopsis)
            media.start_date = start_date or media.start_date
            media.end_date = end_date or media.end_date
            media.status = status_enum or media.status
            media.score = data.get("score", media.score)
            media.votes = data.get("votes", media.votes)
            media.backdrop_url = data.get("backdrop", media.backdrop_url)
            media.trailer_url = data.get("trailer", media.trailer_url)
            media.image_url = data.get("poster", media.image_url)
            media.watch_url = data.get("watch_url", media.watch_url)
            media.seasons = data.get("seasons", media.seasons)
            media.mature = data.get("mature", media.mature)
            media.featured = data.get("featured", media.featured)
            media.updated_at = updated_at or media.updated_at

        # Procesar géneros
        for g in data.get("genres", []):
            genre = db.query(Genre).filter(Genre.slug == g["slug"]).first()
            if not genre:
                genre = Genre(
                    name=g["name"],
                    slug=g["slug"],
                    added_at=datetime.utcnow()
                )
                db.add(genre)
                db.commit()
            assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
            if not assoc:
                assoc = MediaGenre(media_id=media.id, genre_id=genre.id, added_at=datetime.utcnow())
                db.add(assoc)

        # Procesar tags
        for t in data.get("tags", []):
            tag = db.query(Tag).filter(Tag.slug == t.get("slug", slugify(t.get("name", "")))).first()
            if not tag:
                tag = Tag(
                    name=t.get("name", "Unknown"),
                    slug=t.get("slug", slugify(t.get("name", "unknown"))),
                    added_at=datetime.utcnow()
                )
                db.add(tag)
                db.commit()
            assoc = db.query(MediaTag).filter(MediaTag.media_id == media.id, MediaTag.tag_id == tag.id).first()
            if not assoc:
                assoc = MediaTag(media_id=media.id, tag_id=tag.id, added_at=datetime.utcnow())
                db.add(assoc)

        # Procesar content_units (episodios)
        for ep in data.get("episodes", []):
            ep_id = ep.get("id")
            content_unit = db.query(ContentUnit).filter(ContentUnit.id == ep_id).first() if ep_id else None
            if not content_unit:
                content_unit = db.query(ContentUnit).filter(ContentUnit.media_id == media.id, ContentUnit.number == ep["number"]).first()
            if not content_unit:
                content_unit = ContentUnit(
                    id=ep_id,
                    media_id=media.id,
                    type="episode",
                    number=ep["number"],
                    image_url=ep.get("image"),
                    url=ep.get("url"),
                    is_filler=ep.get("filler", False),
                    created_at=datetime.utcnow()
                )
                db.add(content_unit)
            else:
                content_unit.image_url = ep.get("image") or content_unit.image_url
                content_unit.url = ep.get("url") or content_unit.url
                content_unit.is_filler = ep.get("filler", content_unit.is_filler)
            db.commit()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

# Función para guardar Anime Episode
def save_anime_episode(data: dict):
    status_map = {
        1: MediaStatus.EMISION,
        2: MediaStatus.FINALIZADO,
        3: MediaStatus.PROXIMAMENTE
    }
    db = next(get_db())
    try:
        anime_data = data.get("anime")
        mt_name = anime_data.get("category", {}).get("name", "tv-anime")
        media_type = db.query(MediaType).filter(MediaType.name == mt_name).first()
        if not media_type:
            media_type = MediaType(
                name=mt_name,
                description=f"Tipo {mt_name}",
                added_at=datetime.utcnow()
            )
            db.add(media_type)
            db.commit()

        status_val = anime_data.get("status")
        status_enum = status_map.get(status_val) if isinstance(status_val, int) else MediaStatus(status_val) if status_val else None

        media = db.query(Media).filter(Media.id == anime_data["id"]).first()
        if not media:
            media = Media(
                id=anime_data["id"],
                title=anime_data["title"],
                alternative_titles=anime_data.get("aka"),
                score=anime_data.get("score"),
                votes=anime_data.get("votes"),
                status=status_enum,
                media_type_id=media_type.id,
                created_at=datetime.utcnow()
            )
            db.add(media)
        else:
            media.score = anime_data.get("score", media.score)
            media.votes = anime_data.get("votes", media.votes)
            media.status = status_enum or media.status

        for genre_name in anime_data.get("genres", []):
            genre = db.query(Genre).filter(Genre.name == genre_name).first()
            if not genre:
                genre = Genre(
                    name=genre_name,
                    slug=slugify(genre_name),
                    added_at=datetime.utcnow()
                )
                db.add(genre)
                db.commit()
            assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
            if not assoc:
                assoc = MediaGenre(media_id=media.id, genre_id=genre.id, added_at=datetime.utcnow())
                db.add(assoc)

        ep_data = data.get("episode")
        content_unit = db.query(ContentUnit).filter(ContentUnit.id == ep_data["id"]).first()
        if not content_unit:
            content_unit_by_key = db.query(ContentUnit).filter(ContentUnit.media_id == media.id, ContentUnit.number == ep_data["number"]).first()
            image_url = content_unit_by_key.image_url if content_unit_by_key else None
            url = content_unit_by_key.url if content_unit_by_key else None
            if content_unit_by_key and content_unit_by_key.id < 100000:  # Umbral para detectar placeholders
                db.delete(content_unit_by_key)
                db.commit()
            content_unit = ContentUnit(
                id=ep_data["id"],
                media_id=media.id,
                type="episode",
                number=ep_data["number"],
                is_filler=ep_data.get("filler", False),
                image_url=image_url,
                url=url,
                created_at=datetime.utcnow()
            )
            db.add(content_unit)
        else:
            content_unit.is_filler = ep_data.get("filler", content_unit.is_filler)
            content_unit.image_url = ep_data.get("image") or content_unit.image_url
            content_unit.url = ep_data.get("url") or content_unit.url

        for emb in data.get("embeds", []):
            embed = db.query(Embed).filter(Embed.content_unit_id == content_unit.id, Embed.server == emb["server"], Embed.url == emb["url"]).first()
            if not embed:
                embed = Embed(
                    content_unit_id=content_unit.id,
                    server=emb["server"],
                    url=emb["url"],
                    variant=emb.get("variant"),
                    added_at=datetime.utcnow()
                )
                db.add(embed)

        for dl in data.get("downloads", []):
            download = db.query(Download).filter(Download.content_unit_id == content_unit.id, Download.server == dl["server"], Download.url == dl["url"]).first()
            if not download:
                download = Download(
                    content_unit_id=content_unit.id,
                    server=dl["server"],
                    url=dl["url"],
                    variant=dl.get("variant"),
                    added_at=datetime.utcnow()
                )
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
            mt_data = item.get("category")
            if mt_data:
                media_type = db.query(MediaType).filter(MediaType.name == mt_data["name"]).first()
                if not media_type:
                    slug = mt_data.get("slug") or generate_slug(mt_data["name"])
                    media_type = MediaType(
                        name=mt_data["name"],
                        description=mt_data.get("description", f"Tipo {mt_data['name']}"),
                        added_at=datetime.utcnow()
                    )
                    db.add(media_type)
                    db.commit()

            start_date = parser.parse(item["startDate"]).date() if item.get("startDate") else None
            created_at = parser.isoparse(item["createdAt"].replace("+00", "Z")) if item.get("createdAt") else datetime.utcnow()
            media = db.query(Media).filter(Media.id == item["id"]).first()
            if not media:
                media = Media(
                    id=item["id"],
                    slug=item["slug"],
                    title=item["title"],
                    synopsis=item.get("synopsis"),
                    start_date=start_date,
                    image_url=item.get("poster"),
                    media_type_id=media_type.id if mt_data else None,
                    created_at=created_at
                )
                db.add(media)
                db.commit()

            le_data = item.get("latestEpisode")
            if le_data:
                created_at_ep = parser.isoparse(le_data["createdAt"].replace("+00:00", "")) if le_data.get("createdAt") else datetime.utcnow()
                content_unit = db.query(ContentUnit).filter(ContentUnit.id == le_data["id"]).first()
                if not content_unit:
                    content_unit = ContentUnit(
                        id=le_data["id"],
                        media_id=media.id,
                        type="episode",
                        number=le_data["number"],
                        created_at=created_at_ep
                    )
                    db.add(content_unit)
                    db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error al guardar en la base de datos: {e}")
        raise
    finally:
        db.close()