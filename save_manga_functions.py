# save_functions.py - Funciones para guardar datos en la base de datos
from database import FilterOption, SessionLocal, Category, Genre, Tag, Media, MediaGenre, MediaTag, Episode, Embed, Download, MediaStatus, get_db
from datetime import datetime
from dateutil import parser
from slugify import slugify
from sqlalchemy.orm import Session
import re


def save_manga_home(data: dict):
    db = next(get_db())
    try:
        # Procesar populares (general, seinen, josei)
        print("Procesando populares...")
        for section, content in data.get("populares", {}).items():
            for item in content.get("items", []):
                try:
                    print(f"Procesando manga {item['title']} ({section})")
                    # Crear o actualizar categoría
                    category = None
                    if section in ["seinen", "josei"]:
                        category = db.query(Category).filter(Category.name == section.capitalize()).first()
                        if not category:
                            print(f"Creando categoría {section}")
                            category = Category(
                                name=section.capitalize(),
                                slug=generate_slug(section),
                                added_at=datetime.utcnow()
                            )
                            db.add(category)
                            db.commit()

                    # Procesar media
                    media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                    media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                    if not media:
                        print(f"Creando manga {item['title']}")
                        media = Media(
                            id=media_id,
                            slug=generate_slug(item["title"]),
                            title=item["title"],
                            image_url=item.get("cover"),
                            watch_url=item.get("url"),
                            score=float(item["score"]) if item.get("score") else None,
                            type=item.get("type", "manga"),
                            category_id=category.id if category else None,
                            added_at=datetime.utcnow(),
                            created_at=datetime.utcnow() if item.get("upload_time") else None
                        )
                        db.add(media)
                        db.commit()
                    else:
                        media.image_url = item.get("cover") or media.image_url
                        media.watch_url = item.get("url") or media.watch_url
                        media.score = float(item["score"]) if item.get("score") else media.score
                        media.type = item.get("type", media.type)
                        media.category_id = category.id if category else media.category_id
                        db.commit()

                    # Procesar demografía como género
                    if item.get("demography"):
                        genre = db.query(Genre).filter(Genre.name == item["demography"]).first()
                        if not genre:
                            print(f"Creando género {item['demography']}")
                            genre = Genre(
                                name=item["demography"],
                                slug=generate_slug(item["demography"]),
                                added_at=datetime.utcnow()
                            )
                            db.add(genre)
                            db.commit()
                        assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
                        if not assoc:
                            print(f"Asociando género {item['demography']} con manga {media.id}")
                            assoc = MediaGenre(
                                media_id=media.id,
                                genre_id=genre.id,
                                added_at=datetime.utcnow()
                            )
                            db.add(assoc)
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
                    category = None
                    if section in ["seinen", "josei"]:
                        category = db.query(Category).filter(Category.name == section.capitalize()).first()
                        if not category:
                            print(f"Creando categoría {section}")
                            category = Category(
                                name=section.capitalize(),
                                slug=generate_slug(section),
                                added_at=datetime.utcnow()
                            )
                            db.add(category)
                            db.commit()

                    media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                    media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                    if not media:
                        print(f"Creando manga {item['title']}")
                        media = Media(
                            id=media_id,
                            slug=generate_slug(item["title"]),
                            title=item["title"],
                            image_url=item.get("cover"),
                            watch_url=item.get("url"),
                            score=float(item["score"]) if item.get("score") else None,
                            type=item.get("type", "manga"),
                            category_id=category.id if category else None,
                            added_at=datetime.utcnow(),
                            created_at=datetime.utcnow() if item.get("upload_time") else None
                        )
                        db.add(media)
                        db.commit()
                    else:
                        media.image_url = item.get("cover") or media.image_url
                        media.watch_url = item.get("url") or media.watch_url
                        media.score = float(item["score"]) if item.get("score") else media.score
                        media.type = item.get("type", media.type)
                        media.category_id = category.id if category else media.category_id
                        db.commit()

                    if item.get("demography"):
                        genre = db.query(Genre).filter(Genre.name == item["demography"]).first()
                        if not genre:
                            print(f"Creando género {item['demography']}")
                            genre = Genre(
                                name=item["demography"],
                                slug=generate_slug(item["demography"]),
                                added_at=datetime.utcnow()
                            )
                            db.add(genre)
                            db.commit()
                        assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
                        if not assoc:
                            print(f"Asociando género {item['demography']} con manga {media.id}")
                            assoc = MediaGenre(
                                media_id=media.id,
                                genre_id=genre.id,
                                added_at=datetime.utcnow()
                            )
                            db.add(assoc)
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
                media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                if not media:
                    print(f"Creando manga {item['title']}")
                    media = Media(
                        id=media_id,
                        slug=generate_slug(item["title"]),
                        title=item["title"],
                        image_url=item.get("cover"),
                        watch_url=item.get("url"),
                        score=float(item["score"]) if item.get("score") else None,
                        type=item.get("type", "manga"),
                        added_at=datetime.utcnow(),
                        created_at=datetime.utcnow() if item.get("upload_time") else None
                    )
                    db.add(media)
                    db.commit()
                else:
                    media.image_url = item.get("cover") or media.image_url
                    media.watch_url = item.get("url") or media.watch_url
                    media.score = float(item["score"]) if item.get("score") else media.score
                    media.type = item.get("type", media.type)
                    db.commit()

                if item.get("demography"):
                    genre = db.query(Genre).filter(Genre.name == item["demography"]).first()
                    if not genre:
                        print(f"Creando género {item['demography']}")
                        genre = Genre(
                            name=item["demography"],
                            slug=generate_slug(item["demography"]),
                            added_at=datetime.utcnow()
                        )
                        db.add(genre)
                        db.commit()
                    assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
                    if not assoc:
                        print(f"Asociando género {item['demography']} con manga {media.id}")
                        assoc = MediaGenre(
                            media_id=media.id,
                            genre_id=genre.id,
                            added_at=datetime.utcnow()
                        )
                        db.add(assoc)
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
                media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                if not media:
                    print(f"Creando manga {item['title']}")
                    media = Media(
                        id=media_id,
                        slug=generate_slug(item["title"]),
                        title=item["title"],
                        image_url=item.get("cover"),
                        watch_url=item.get("url"),
                        score=float(item["score"]) if item.get("score") else None,
                        type=item.get("type", "manga"),
                        added_at=datetime.utcnow(),
                        created_at=datetime.utcnow() if item.get("upload_time") else None,
                        episodes_count=int(item["chapter"]) if item.get("chapter") else None
                    )
                    db.add(media)
                    db.commit()
                else:
                    media.image_url = item.get("cover") or media.image_url
                    media.watch_url = item.get("url") or media.watch_url
                    media.score = float(item["score"]) if item.get("score") else media.score
                    media.type = item.get("type", media.type)
                    media.episodes_count = int(item["chapter"]) if item.get("chapter") else media.episodes_count
                    db.commit()

                if item.get("demography"):
                    genre = db.query(Genre).filter(Genre.name == item["demography"]).first()
                    if not genre:
                        print(f"Creando género {item['demography']}")
                        genre = Genre(
                            name=item["demography"],
                            slug=generate_slug(item["demography"]),
                            added_at=datetime.utcnow()
                        )
                        db.add(genre)
                        db.commit()
                    assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
                    if not assoc:
                        print(f"Asociando género {item['demography']} con manga {media.id}")
                        assoc = MediaGenre(
                            media_id=media.id,
                            genre_id=genre.id,
                            added_at=datetime.utcnow()
                        )
                        db.add(assoc)
                        db.commit()

                # Procesar capítulo como episodio
                if item.get("chapter"):
                    episode = db.query(Episode).filter(Episode.media_id == media.id, Episode.number == int(item["chapter"])).first()
                    if not episode:
                        print(f"Creando capítulo {item['chapter']} para manga {media.id}")
                        episode = Episode(
                            media_id=media.id,
                            number=int(item["chapter"]),
                            watch_url=item.get("url"),
                            added_at=datetime.utcnow()
                        )
                        db.add(episode)
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
                media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                if not media:
                    print(f"Creando manga {item['title']}")
                    media = Media(
                        id=media_id,
                        slug=generate_slug(item["title"]),
                        title=item["title"],
                        watch_url=item.get("url"),
                        type=item.get("type", "manga"),
                        added_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()
                else:
                    media.watch_url = item.get("url") or media.watch_url
                    media.type = item.get("type", media.type)
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
                media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                if not media:
                    print(f"Creando manga {item['title']}")
                    media = Media(
                        id=media_id,
                        slug=generate_slug(item["title"]),
                        title=item["title"],
                        watch_url=item.get("url"),
                        type=item.get("type", "manga"),
                        added_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()
                else:
                    media.watch_url = item.get("url") or media.watch_url
                    media.type = item.get("type", media.type)
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


def save_manga_search(data: dict):
    db = next(get_db())
    status_map = {
        "publishing": MediaStatus.EMISION,
        "ended": MediaStatus.FINALIZADO,
        "cancelled": MediaStatus.FINALIZADO,  # Podrías mapear "cancelled" a un nuevo valor en MediaStatus si lo prefieres
        "on_hold": MediaStatus.PROXIMAMENTE
    }
    try:
        print("Procesando resultados de búsqueda de mangas...")
        for item in data.get("results", []):
            try:
                print(f"Procesando manga {item['title']}")
                # Crear o actualizar categoría basada en demografía
                category = None
                if item.get("demography") and item["demography"] != "Unknown":
                    category = db.query(Category).filter(Category.name == item["demography"]).first()
                    if not category:
                        print(f"Creando categoría {item['demography']}")
                        category = Category(
                            name=item["demography"],
                            slug=generate_slug(item["demography"]),
                            added_at=datetime.utcnow()
                        )
                        db.add(category)
                        db.commit()

                # Procesar media
                media_id = int(re.search(r'\d+', item["url"]).group()) if item.get("url") and re.search(r'\d+', item["url"]) else None
                media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                if not media:
                    print(f"Creando manga {item['title']}")
                    media = Media(
                        id=media_id,
                        slug=generate_slug(item["title"]),
                        title=item["title"],
                        image_url=item.get("image_url") if item["image_url"] != "Unknown" else None,
                        watch_url=item.get("url"),
                        score=float(item["score"]) if item.get("score") else None,
                        type=item.get("type", "manga") if item["type"] != "Unknown" else "manga",
                        category_id=category.id if category else None,
                        added_at=datetime.utcnow(),
                        mature=item.get("is_erotic", False)
                    )
                    db.add(media)
                    db.commit()
                else:
                    media.image_url = (item.get("image_url") or media.image_url) if item["image_url"] != "Unknown" else media.image_url
                    media.watch_url = item.get("url") or media.watch_url
                    media.score = float(item["score"]) if item.get("score") else media.score
                    media.type = item.get("type", media.type) if item["type"] != "Unknown" else media.type
                    media.category_id = category.id if category else media.category_id
                    media.mature = item.get("is_erotic", media.mature)
                    db.commit()

                # Procesar demografía como género
                if item.get("demography") and item["demography"] != "Unknown":
                    genre = db.query(Genre).filter(Genre.name == item["demography"]).first()
                    if not genre:
                        print(f"Creando género {item['demography']}")
                        genre = Genre(
                            name=item["demography"],
                            slug=generate_slug(item["demography"]),
                            added_at=datetime.utcnow()
                        )
                        db.add(genre)
                        db.commit()
                    assoc = db.query(MediaGenre).filter(MediaGenre.media_id == media.id, MediaGenre.genre_id == genre.id).first()
                    if not assoc:
                        print(f"Asociando género {item['demography']} con manga {media.id}")
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


def save_manga_filters(data: dict):
    """
    Guarda las opciones de filtros de mangas en la tabla filter_options.
    
    Args:
        data (dict): Diccionario con los filtros y sus opciones, como el retornado por el endpoint /filters.
        db (Session): Sesión de la base de datos.
    """
    db = next(get_db())
    try:
        print("Procesando filtros de mangas...")
        for filter_type, filter_info in data.get("filters", {}).items():
            try:
                is_multiple = filter_info.get("type") == "list"
                values = filter_info.get("values", [])
                if not values and filter_type == "title":
                    # El campo 'title' no tiene valores predefinidos, es texto libre
                    continue
                for value in values:
                    try:
                        # Verificar si el filtro ya existe
                        option = db.query(FilterOption).filter(
                            FilterOption.filter_type == filter_type,
                            FilterOption.value == value
                        ).first()
                        if not option:
                            print(f"Guardando filtro {filter_type}: {value}")
                            option = FilterOption(
                                filter_type=filter_type,
                                value=value,
                                is_multiple=is_multiple,
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