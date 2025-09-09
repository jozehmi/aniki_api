from sqlalchemy.exc import IntegrityError
from database import FilterOption, SessionLocal, MediaType, DemographyType, Genre,Media, ContentUnit, Embed, Download, MediaStatus, get_db
from datetime import datetime
from dateutil import parser
from slugify import slugify
from sqlalchemy.orm import Session
import re

# Función auxiliar para generar un slug
def generate_slug(name: str) -> str:
    """Convierte un nombre en un slug (minúsculas, sin espacios, solo caracteres alfanuméricos y guiones)."""
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower()).replace(' ', '-')
    return slug or 'default-slug'  # Fallback si el nombre está vacío

# Función para guardar Manga Home
def save_manga_home(data: dict):
    db = next(get_db())
    status_map = {
        "publishing": MediaStatus.PUBLISHING,
        "finished": MediaStatus.FINISHED,
        "canceled": MediaStatus.CANCELADO,
        "paused": MediaStatus.PAUSADO
    }
    try:
        # Procesar populares (general, seinen, josei)
        print("Procesando populares...")
        for section, content in data.get("populares", {}).items():
            for item in content.get("items", []):
                try:
                    print(f"Procesando manga {item['title']} ({section})")
                    # Crear o actualizar MediaType
                    mt_name = item.get("type", "manga").lower()
                    media_type = db.query(MediaType).filter(MediaType.name == mt_name).first()
                    if not media_type:
                        print(f"Creando media_type {mt_name}")
                        media_type = MediaType(
                            name=mt_name,
                            description=f"Tipo {mt_name.capitalize()}",
                            added_at=datetime.utcnow()
                        )
                        db.add(media_type)
                        db.commit()

                    # Crear o actualizar DemographyType
                    demography = None
                    if item.get("demography") and item["demography"].lower() in ["seinen", "shoujo", "shounen", "josei", "kodomo"]:
                        demography = db.query(DemographyType).filter(DemographyType.name == item["demography"].lower()).first()
                        if not demography:
                            print(f"Creando demografía {item['demography']}")
                            demography = DemographyType(
                                name=item["demography"].lower(),
                                description=f"Demografía {item['demography']}",
                                added_at=datetime.utcnow()
                            )
                            db.add(demography)
                            db.commit()

                    # Procesar media
                    media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                    media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                    if not media:
                        print(f"Creando manga {item['title']}")
                        media = Media(
                            id=media_id,
                            slug=item.get("slug", generate_slug(item["title"])),
                            title=item["title"],
                            image_url=item.get("cover"),
                            source_url=item.get("url"),
                            score=float(item["score"]) if item.get("score") and item["score"] != "Unknown" else None,
                            media_type_id=media_type.id,
                            demography_id=demography.id if demography else None,
                            status=status_map.get(item.get("status", "").lower()),
                            added_at=datetime.utcnow(),
                            created_at=parser.isoparse(item["upload_time"]) if item.get("upload_time") else datetime.utcnow(),
                            featured=True
                        )
                        db.add(media)
                        db.commit()
                    else:
                        media.image_url = item.get("cover") or media.image_url
                        media.source_url = item.get("url") or media.source_url
                        media.score = float(item["score"]) if item.get("score") and item["score"] != "Unknown" else media.score
                        media.media_type_id = media_type.id
                        media.demography_id = demography.id if demography else media.demography_id
                        media.status = status_map.get(item.get("status", "").lower(), media.status)
                        db.commit()

                except Exception as e:
                    print(f"Error procesando item {item.get('title', 'unknown')} en populares: {e}")
                    db.rollback()
                    continue

        # Procesar trending (general, seinen, josei)
        print("Procesando trending...")
        for section, content in data.get("trending", {}).items():
            for item in content.get("items", []):
                try:
                    print(f"Procesando manga {item['title']} ({section})")
                    mt_name = item.get("type", "manga").lower()
                    media_type = db.query(MediaType).filter(MediaType.name == mt_name).first()
                    if not media_type:
                        print(f"Creando media_type {mt_name}")
                        media_type = MediaType(
                            name=mt_name,
                            description=f"Tipo {mt_name.capitalize()}",
                            added_at=datetime.utcnow()
                        )
                        db.add(media_type)
                        db.commit()

                    demography = None
                    if item.get("demography") and item["demography"].lower() in ["seinen", "shoujo", "shounen", "josei", "kodomo"]:
                        demography = db.query(DemographyType).filter(DemographyType.name == item["demography"].lower()).first()
                        if not demography:
                            print(f"Creando demografía {item['demography']}")
                            demography = DemographyType(
                                name=item["demography"].lower(),
                                description=f"Demografía {item['demography']}",
                                added_at=datetime.utcnow()
                            )
                            db.add(demography)
                            db.commit()

                    media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                    media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                    if not media:
                        print(f"Creando manga {item['title']}")
                        media = Media(
                            id=media_id,
                            slug=item.get("slug", generate_slug(item["title"])),
                            title=item["title"],
                            image_url=item.get("cover"),
                            source_url=item.get("url"),
                            score=float(item["score"]) if item.get("score") and item["score"] != "Unknown" else None,
                            media_type_id=media_type.id,
                            demography_id=demography.id if demography else None,
                            status=status_map.get(item.get("status", "").lower()),
                            added_at=datetime.utcnow(),
                            created_at=parser.isoparse(item["upload_time"]) if item.get("upload_time") else datetime.utcnow()
                        )
                        db.add(media)
                        db.commit()
                    else:
                        media.image_url = item.get("cover") or media.image_url
                        media.source_url = item.get("url") or media.source_url
                        media.score = float(item["score"]) if item.get("score") and item["score"] != "Unknown" else media.score
                        media.media_type_id = media_type.id
                        media.demography_id = demography.id if demography else media.demography_id
                        media.status = status_map.get(item.get("status", "").lower(), media.status)
                        db.commit()

                except Exception as e:
                    print(f"Error procesando item {item.get('title', 'unknown')} en trending: {e}")
                    db.rollback()
                    continue

        # Procesar últimos añadidos
        print("Procesando ultimos_anadidos...")
        for item in data.get("ultimos_anadidos", {}).get("items", []):
            try:
                print(f"Procesando manga {item['title']}")
                mt_name = item.get("type", "manga").lower()
                media_type = db.query(MediaType).filter(MediaType.name == mt_name).first()
                if not media_type:
                    print(f"Creando media_type {mt_name}")
                    media_type = MediaType(
                        name=mt_name,
                        description=f"Tipo {mt_name.capitalize()}",
                        added_at=datetime.utcnow()
                    )
                    db.add(media_type)
                    db.commit()

                demography = None
                if item.get("demography") and item["demography"].lower() in ["seinen", "shoujo", "shounen", "josei", "kodomo"]:
                    demography = db.query(DemographyType).filter(DemographyType.name == item["demography"].lower()).first()
                    if not demography:
                        print(f"Creando demografía {item['demography']}")
                        demography = DemographyType(
                            name=item["demography"].lower(),
                            description=f"Demografía {item['demography']}",
                            added_at=datetime.utcnow()
                        )
                        db.add(demography)
                        db.commit()

                media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                if not media:
                    print(f"Creando manga {item['title']}")
                    media = Media(
                        id=media_id,
                        slug=item.get("slug", generate_slug(item["title"])),
                        title=item["title"],
                        image_url=item.get("cover"),
                        source_url=item.get("url"),
                        score=float(item["score"]) if item.get("score") and item["score"] != "Unknown" else None,
                        media_type_id=media_type.id,
                        demography_id=demography.id if demography else None,
                        status=status_map.get(item.get("status", "").lower()),
                        added_at=datetime.utcnow(),
                        created_at=parser.isoparse(item["upload_time"]) if item.get("upload_time") else datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()
                else:
                    media.image_url = item.get("cover") or media.image_url
                    media.source_url = item.get("url") or media.source_url
                    media.score = float(item["score"]) if item.get("score") and item["score"] != "Unknown" else media.score
                    media.media_type_id = media_type.id
                    media.demography_id = demography.id if demography else media.demography_id
                    media.status = status_map.get(item.get("status", "").lower(), media.status)
                    db.commit()

            except Exception as e:
                print(f"Error procesando item {item.get('title', 'unknown')} en ultimos_anadidos: {e}")
                db.rollback()
                continue

        # Procesar últimas subidas
        print("Procesando ultimas_subidas...")
        for item in data.get("ultimas_subidas", {}).get("items", []):
            try:
                print(f"Procesando manga {item['title']}")
                mt_name = item.get("type", "manga").lower()
                media_type = db.query(MediaType).filter(MediaType.name == mt_name).first()
                if not media_type:
                    print(f"Creando media_type {mt_name}")
                    media_type = MediaType(
                        name=mt_name,
                        description=f"Tipo {mt_name.capitalize()}",
                        added_at=datetime.utcnow()
                    )
                    db.add(media_type)
                    db.commit()

                demography = None
                if item.get("demography") and item["demography"].lower() in ["seinen", "shoujo", "shounen", "josei", "kodomo"]:
                    demography = db.query(DemographyType).filter(DemographyType.name == item["demography"].lower()).first()
                    if not demography:
                        print(f"Creando demografía {item['demography']}")
                        demography = DemographyType(
                            name=item["demography"].lower(),
                            description=f"Demografía {item['demography']}",
                            added_at=datetime.utcnow()
                        )
                        db.add(demography)
                        db.commit()

                media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                if not media:
                    print(f"Creando manga {item['title']}")
                    media = Media(
                        id=media_id,
                        slug=item.get("slug", generate_slug(item["title"])),
                        title=item["title"],
                        image_url=item.get("cover"),
                        source_url=item.get("url"),
                        score=float(item["score"]) if item.get("score") and item["score"] != "Unknown" else None,
                        media_type_id=media_type.id,
                        demography_id=demography.id if demography else None,
                        status=status_map.get(item.get("status", "").lower()),
                        added_at=datetime.utcnow(),
                        created_at=parser.isoparse(item["upload_time"]) if item.get("upload_time") else datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()
                else:
                    media.image_url = item.get("cover") or media.image_url
                    media.source_url = item.get("url") or media.source_url
                    media.score = float(item["score"]) if item.get("score") and item["score"] != "Unknown" else media.score
                    media.media_type_id = media_type.id
                    media.demography_id = demography.id if demography else media.demography_id
                    media.status = status_map.get(item.get("status", "").lower(), media.status)
                    db.commit()

                # Procesar capítulo como ContentUnit
                if item.get("chapter"):
                    content_unit = db.query(ContentUnit).filter(ContentUnit.media_id == media.id, ContentUnit.number == float(item["chapter"])).first()
                    if not content_unit:
                        print(f"Creando capítulo {item['chapter']} para manga {media.id}")
                        content_unit = ContentUnit(
                            media_id=media.id,
                            type="chapter",
                            number=float(item["chapter"]),
                            url=item.get("url"),
                            published_at=parser.isoparse(item["upload_time"]) if item.get("upload_time") else datetime.utcnow(),
                            created_at=datetime.utcnow()
                        )
                        db.add(content_unit)
                        db.commit()

            except Exception as e:
                print(f"Error procesando item {item.get('title', 'unknown')} en ultimas_subidas: {e}")
                db.rollback()
                continue

        # Procesar top semanal
        print("Procesando top_semanal...")
        for item in data.get("top_semanal", {}).get("items", []):
            try:
                print(f"Procesando manga {item['title']}")
                mt_name = item.get("type", "manga").lower()
                media_type = db.query(MediaType).filter(MediaType.name == mt_name).first()
                if not media_type:
                    print(f"Creando media_type {mt_name}")
                    media_type = MediaType(
                        name=mt_name,
                        description=f"Tipo {mt_name.capitalize()}",
                        added_at=datetime.utcnow()
                    )
                    db.add(media_type)
                    db.commit()

                media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                if not media:
                    print(f"Creando manga {item['title']}")
                    media = Media(
                        id=media_id,
                        slug=item.get("slug", generate_slug(item["title"])),
                        title=item["title"],
                        source_url=item.get("url"),
                        media_type_id=media_type.id,
                        added_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()
                else:
                    media.source_url = item.get("url") or media.source_url
                    media.media_type_id = media_type.id
                    db.commit()

            except Exception as e:
                print(f"Error procesando item {item.get('title', 'unknown')} en top_semanal: {e}")
                db.rollback()
                continue

        # Procesar top mensual
        print("Procesando top_mensual...")
        for item in data.get("top_mensual", {}).get("items", []):
            try:
                print(f"Procesando manga {item['title']}")
                mt_name = item.get("type", "manga").lower()
                media_type = db.query(MediaType).filter(MediaType.name == mt_name).first()
                if not media_type:
                    print(f"Creando media_type {mt_name}")
                    media_type = MediaType(
                        name=mt_name,
                        description=f"Tipo {mt_name.capitalize()}",
                        added_at=datetime.utcnow()
                    )
                    db.add(media_type)
                    db.commit()

                media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                if not media:
                    print(f"Creando manga {item['title']}")
                    media = Media(
                        id=media_id,
                        slug=item.get("slug", generate_slug(item["title"])),
                        title=item["title"],
                        source_url=item.get("url"),
                        media_type_id=media_type.id,
                        added_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()
                else:
                    media.source_url = item.get("url") or media.source_url
                    media.media_type_id = media_type.id
                    db.commit()

            except Exception as e:
                print(f"Error procesando item {item.get('title', 'unknown')} en top_mensual: {e}")
                db.rollback()
                continue

        db.commit()
        print("Todos los datos de manga procesados y guardados correctamente.")
    except Exception as e:
        db.rollback()
        print(f"Error general en save_manga_home: {e}")
        raise
    finally:
        db.close()

# Función para guardar Manga Search
def save_manga_search(data: dict):
    db = next(get_db())
    status_map = {
        "publishing": MediaStatus.PUBLISHING,
        "ended": MediaStatus.FINISHED,
        "cancelled": MediaStatus.CANCELADO,
        "paused": MediaStatus.PAUSADO,
        "on_hold": MediaStatus.PAUSADO
    }
    translation_status_map = {
        "active": MediaStatus.ACTIVE,
        "finished": MediaStatus.FINISHED,
        "abandoned": MediaStatus.ABANDONED
    }
    try:
        print("Procesando resultados de búsqueda de mangas...")
        for item in data.get("results", []):
            try:
                print(f"Procesando manga {item['title']}")
                # Crear o actualizar MediaType
                mt_name = item.get("type", "manga").lower()
                media_type = db.query(MediaType).filter(MediaType.name == mt_name).first()
                if not media_type:
                    print(f"Creando media_type {mt_name}")
                    media_type = MediaType(
                        name=mt_name,
                        description=f"Tipo {mt_name.capitalize()}",
                        added_at=datetime.utcnow()
                    )
                    db.add(media_type)
                    db.commit()

                # Crear o actualizar DemographyType
                demography = None
                if item.get("demography") and item["demography"].lower() != "unknown" and item["demography"].lower() in ["seinen", "shoujo", "shounen", "josei", "kodomo"]:
                    demography = db.query(DemographyType).filter(DemographyType.name == item["demography"].lower()).first()
                    if not demography:
                        print(f"Creando demografía {item['demography']}")
                        demography = DemographyType(
                            name=item["demography"].lower(),
                            description=f"Demografía {item['demography']}",
                            added_at=datetime.utcnow()
                        )
                        db.add(demography)
                        db.commit()

                # Procesar media
                media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                if not media:
                    print(f"Creando manga {item['title']}")
                    media = Media(
                        id=media_id,
                        slug=item.get("slug", generate_slug(item["title"])),
                        title=item["title"],
                        image_url=item.get("image_url") if item.get("image_url") != "Unknown" else None,
                        source_url=item.get("url"),
                        score=float(item["score"]) if item.get("score") and item["score"] != "Unknown" else None,
                        media_type_id=media_type.id,
                        demography_id=demography.id if demography else None,
                        status=status_map.get(item.get("status", "").lower()),
                        translation_status=translation_status_map.get(item.get("translation_status", "").lower()),
                        mature=item.get("is_erotic", False),
                        webcomic=item.get("webcomic") == "yes" if item.get("webcomic") else False,
                        yonkoma=item.get("yonkoma") == "yes" if item.get("yonkoma") else False,
                        amateur=item.get("amateur") == "yes" if item.get("amateur") else False,
                        added_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()
                else:
                    media.image_url = (item.get("image_url") or media.image_url) if item.get("image_url") != "Unknown" else media.image_url
                    media.source_url = item.get("url") or media.source_url
                    media.score = float(item["score"]) if item.get("score") and item["score"] != "Unknown" else media.score
                    media.media_type_id = media_type.id
                    media.demography_id = demography.id if demography else media.demography_id
                    media.status = status_map.get(item.get("status", "").lower(), media.status)
                    media.translation_status = translation_status_map.get(item.get("translation_status", "").lower(), media.translation_status)
                    media.mature = item.get("is_erotic", media.mature)
                    media.webcomic = item.get("webcomic") == "yes" if item.get("webcomic") else media.webcomic
                    media.yonkoma = item.get("yonkoma") == "yes" if item.get("yonkoma") else media.yonkoma
                    media.amateur = item.get("amateur") == "yes" if item.get("amateur") else media.amateur
                    db.commit()

                # Procesar géneros
                for genre_name in item.get("genres", []):
                    if genre_name.lower() != "unknown":
                        genre = db.query(Genre).filter(Genre.slug == generate_slug(genre_name)).first()
                        if not genre:
                            print(f"Creando género {genre_name}")
                            genre = Genre(
                                name=genre_name,
                                slug=generate_slug(genre_name),
                                added_at=datetime.utcnow()
                            )
                            db.add(genre)
                            db.commit()
                        assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
                        if not assoc:
                            print(f"Asociando género {genre_name} con manga {media.id}")
                            assoc = MediaGenre(
                                media_id=media.id,
                                genre_id=genre.id,
                                added_at=datetime.utcnow()
                            )
                            db.add(assoc)
                            db.commit()

                # Procesar is_erotic como tag
                if item.get("is_erotic"):
                    tag = db.query(Tag).filter(Tag.name == "Erotic").first()
                    if not tag:
                        print("Creando tag Erotic")
                        tag = Tag(
                            name="Erotic",
                            slug="erotic",
                            added_at=datetime.utcnow()
                        )
                        db.add(tag)
                        db.commit()
                    assoc = db.query(MediaTag).filter(MediaTag.media_id == media.id, MediaTag.tag_id == tag.id).first()
                    if not assoc:
                        print(f"Asociando tag Erotic con manga {media.id}")
                        assoc = MediaTag(
                            media_id=media.id,
                            tag_id=tag.id,
                            added_at=datetime.utcnow()
                        )
                        db.add(assoc)
                        db.commit()

            except Exception as e:
                print(f"Error procesando item {item.get('title', 'unknown')} en búsqueda: {e}")
                db.rollback()
                continue

        db.commit()
        print("Todos los datos de búsqueda de mangas procesados y guardados correctamente.")
    except Exception as e:
        db.rollback()
        print(f"Error general en save_manga_search: {e}")
        raise
    finally:
        db.close()

# Función para guardar Manga Filters
def save_manga_filters(data: dict):
    """
    Guarda las opciones de filtros de mangas en la tabla filter_options.
    
    Args:
        data (dict): Diccionario con los filtros y sus opciones, como el retornado por el endpoint /filters.
    """
    db = next(get_db())
    try:
        print("Procesando filtros de mangas...")
        for filter_type, filter_info in data.get("filters", {}).items():
            try:
                values = filter_info.get("values", [])
                if not values and filter_type == "title":
                    continue  # El campo 'title' es texto libre
                for value in values:
                    try:
                        option = db.query(FilterOption).filter(
                            FilterOption.filter_type == filter_type,
                            FilterOption.value == value
                        ).first()
                        if not option:
                            print(f"Guardando filtro {filter_type}: {value}")
                            option = FilterOption(
                                filter_type=filter_type,
                                value=value,
                                description=filter_info.get("description"),
                                added_at=datetime.utcnow()
                            )
                            db.add(option)
                            db.commit()
                        else:
                            print(f"Filtro {filter_type}: {value} ya existe")
                    except IntegrityError:
                        db.rollback()
                        print(f"Filtro {filter_type}: {value} ya existe (conflicto de unicidad)")
                    except Exception as e:
                        db.rollback()
                        print(f"Error al guardar filtro {filter_type}: {value}: {e}")
            except Exception as e:
                print(f"Error procesando filtro {filter_type}: {e}")
                continue
        print("Todos los filtros de mangas procesados y guardados correctamente.")
    except Exception as e:
        db.rollback()
        print(f"Error general al guardar filtros de mangas: {e}")
        raise
    finally:
        db.close()