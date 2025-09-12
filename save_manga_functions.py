from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
from dateutil import parser
from sqlalchemy.orm import Session
import re
from sqlalchemy import or_

# Importar clases del nuevo esquema de aniki.py
from aniki import (
    MangaFilterOption as FilterOption,
    Genre,
    Manga,
    Chapter,
    Embed,
    Download,
    MangaHomeSection,
    MangaHomeItem,
    Category,
    MangaStatusEnum,
    MangaTranslationStatusEnum,
    YesNoEnum,
    get_db,
    MediaTypeEnum
)

# Función auxiliar para generar un slug
def generate_slug(name: str) -> str:
    """Convierte un nombre en un slug (minúsculas, sin espacios, solo caracteres alfanuméricos y guiones)."""
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower()).replace(' ', '-').strip('-')
    return slug or 'default-slug'  # Fallback si el nombre está vacío

# Función para guardar Manga Home
from sqlalchemy.exc import IntegrityError
import re
from datetime import datetime, timedelta, timezone

def save_manga_home(data: dict):
    db = next(get_db())
    status_map = {
        "publishing": MangaStatusEnum.publishing,
        "finished": MangaStatusEnum.finished,
        "canceled": MangaStatusEnum.canceled,
        "paused": MangaStatusEnum.paused
    }
    translation_status_map = {
        "active": MangaTranslationStatusEnum.active,
        "finished": MangaTranslationStatusEnum.finished,
        "abandoned": MangaTranslationStatusEnum.abandoned
    }
    yes_no_map = {
        "yes": YesNoEnum.yes,
        "no": YesNoEnum.no
    }
    
    # Mapa de secciones basado en el JSON
    section_map = {
        "populares.general": 1,
        "populares.seinen": 2,
        "populares.josei": 3,
        "trending.general": 4,
        "trending.seinen": 5,
        "trending.josei": 6,
        "ultimos_anadidos": 7,
        "ultimas_subidas": 8,
        "top_semanal": 9,
        "top_mensual": 10
    }

    def get_or_create_category(manga_type: str):
        """Obtiene o crea una categoría basada en el tipo de manga."""
        type_to_slug = {
            "manga": "manga",
            "manhua": "manhua",
            "manhwa": "manhwa",
            "novel": "novel",
            "novela": "novel",
            "one_shot": "one_shot",
            "one shot": "one_shot",
            "doujinshi": "doujinshi",
            "oel": "oel"
        }
        slug = type_to_slug.get(manga_type.lower() if manga_type else "manga", "manga")
        category = db.query(Category).filter(
            Category.slug == slug,
            Category.media_type == MediaTypeEnum.manga
        ).first()
        if not category:
            category = Category(
                name=manga_type.capitalize() if manga_type else "Manga",
                slug=slug,
                media_type=MediaTypeEnum.manga
            )
            db.add(category)
            db.flush()
            print(f"Categoría creada: {category.id} - {category.name}")
        return category

    try:
        for section_key in ["populares", "trending", "ultimos_anadidos", "ultimas_subidas", "top_semanal", "top_mensual"]:
            print(f"Procesando {section_key}...")
            section_data = data.get(section_key, {})
            
            # Manejar subsecciones para populares y trending
            subsections = []
            if section_key in ["populares", "trending"]:
                for subkey in ["general", "seinen", "josei"]:
                    if subkey in section_data:
                        subsections.append((f"{section_key}.{subkey}", section_data[subkey]))
            else:
                subsections = [(section_key, section_data)]

            for section_name, section_content in subsections:
                section_id = section_map.get(section_name)
                if not section_id:
                    print(f"Sección {section_name} no encontrada en map.")
                    continue
                
                items = section_content.get("items", [])
                # Deduplicar items en ultimas_subidas por manga_id y chapter
                if section_name == "ultimas_subidas":
                    seen = set()
                    unique_items = []
                    for item in items:
                        media_id_match = re.search(r'/(\d+)/', item.get("url", "")) if item.get("url") else None
                        media_id = int(media_id_match.group(1)) if media_id_match else None
                        chapter = item.get("chapter")
                        key = (media_id, chapter)
                        if key not in seen and media_id is not None:
                            seen.add(key)
                            unique_items.append(item)
                    items = unique_items
                
                for position, item in enumerate(items, 1):
                    try:
                        title = item.get("title", "Unknown").replace("MANGA", "").replace("MANHWA", "").strip()
                        print(f"Procesando manga {title} ({section_name})")
                        
                        # Extraer ID de la URL
                        media_id_match = re.search(r'/(\d+)/', item.get("url", "")) if item.get("url") else None
                        media_id = int(media_id_match.group(1)) if media_id_match else None
                        if not media_id:
                            print(f"URL inválida o ausente para {title}, omitiendo.")
                            continue
                        
                        # Obtener categoría
                        category = get_or_create_category(item.get("type", "manga"))
                        
                        # Parsear upload_time
                        upload_time = item.get("upload_time")
                        created_at = datetime.now(tz=timezone(timedelta(hours=2)))  # CEST timezone
                        if upload_time and upload_time != "0 h":
                            try:
                                hours = int(re.search(r'(\d+)', upload_time).group(1)) if re.search(r'(\d+)', upload_time) else 0
                                created_at = created_at - timedelta(hours=hours)
                            except Exception as e:
                                print(f"Error al parsear upload_time '{upload_time}' para {title}: {e}")
                                created_at = datetime.now(tz=timezone(timedelta(hours=2)))
                        
                        # Buscar o crear Manga
                        manga = db.query(Manga).filter(Manga.id == media_id).first()
                        if not manga:
                            manga = Manga(
                                id=media_id,
                                title=title,
                                subtitle=None,
                                description=None,
                                cover_url=item.get("cover"),
                                type=item.get("type", "manga"),
                                demography=item.get("demography", "") if item.get("demography") else "",
                                state=None,
                                status=status_map.get(item.get("status", "").lower(), MangaStatusEnum.publishing),
                                translation_status=translation_status_map.get(item.get("translation_status", "").lower(), MangaTranslationStatusEnum.active),
                                webcomic=yes_no_map.get(item.get("webcomic", "no"), YesNoEnum.no),
                                yonkoma=yes_no_map.get(item.get("yonkoma", "no"), YesNoEnum.no),
                                amateur=yes_no_map.get(item.get("amateur", "no"), YesNoEnum.no),
                                erotic=yes_no_map.get(item.get("erotic", "no"), YesNoEnum.no),
                                score=float(item["score"]) if item.get("score") and item["score"] != "0.00" else None,
                                popularity=int(item["popularity"]) if item.get("popularity") is not None else 0,
                                url=item.get("url"),
                                alt_titles=[],
                                synonyms=[],
                                category_id=category.id,
                                created_at=created_at,
                                updated_at=created_at
                            )
                            db.add(manga)
                            db.flush()
                            print(f"Manga creado: {manga.id} - {manga.title}")
                        else:
                            manga.title = title
                            manga.cover_url = item.get("cover", manga.cover_url)
                            manga.type = item.get("type", manga.type)
                            manga.demography = item.get("demography", manga.demography) if item.get("demography") else manga.demography
                            manga.status = status_map.get(item.get("status", "").lower(), manga.status)
                            manga.translation_status = translation_status_map.get(item.get("translation_status", "").lower(), manga.translation_status)
                            manga.score = float(item["score"]) if item.get("score") and item["score"] != "0.00" else manga.score
                            manga.popularity = int(item["popularity"]) if item.get("popularity") is not None else manga.popularity
                            manga.url = item.get("url", manga.url)
                            manga.category_id = category.id
                            manga.updated_at = created_at
                        
                        # Géneros (vacíos en el JSON, pero si en el futuro hay, se puede agregar)
                        if not manga.genres:
                            manga.genres = []
                        
                        # Procesar capítulo para ultimas_subidas y ultimos_anadidos
                        chapter_number = None
                        if section_name in ["ultimas_subidas", "ultimos_anadidos"] and item.get("chapter"):
                            chapter_number = float(item["chapter"]) if item.get("chapter") else None
                            print(f"Procesando capítulo {chapter_number} para {title} en {section_name}")
                            # Para ultimas_subidas, crear el capítulo incluso sin chapter_url (permitir url=None)
                            chapter_url = item.get("url")  # Usamos la URL del manga como fallback, ya que no hay URL específica de capítulo en el JSON
                            if chapter_number is not None:
                                chapter = db.query(Chapter).filter(
                                    Chapter.manga_id == manga.id,
                                    Chapter.number == chapter_number
                                ).first()
                                if not chapter:
                                    chapter = Chapter(
                                        manga_id=manga.id,
                                        number=chapter_number,
                                        title=item.get("chapter_title") or f"Capítulo {chapter_number}",
                                        url=chapter_url,  # URL del manga como fallback; puede ajustarse más tarde con scraper de detalle
                                        date=created_at.date() if created_at else None,
                                        group=item.get("group") or "Unknown",
                                        created_at=created_at
                                    )
                                    db.add(chapter)
                                    db.flush()
                                    print(f"Capítulo creado: {chapter_number} para manga {manga.id}")
                                else:
                                    # Actualizar capítulo existente
                                    chapter.title = item.get("chapter_title", chapter.title) or f"Capítulo {chapter_number}"
                                    chapter.url = chapter_url or chapter.url
                                    chapter.date = created_at.date() if created_at else chapter.date
                                    chapter.group = item.get("group", chapter.group) or "Unknown"
                                    print(f"Capítulo {chapter_number} actualizado para manga {manga.id}")
                            else:
                                print(f"No se puede crear capítulo para {title}: chapter_number inválido")
                        
                        # Añadir a MangaHomeItem
                        position = item.get("position", position)
                        existing_home_item = db.query(MangaHomeItem).filter(
                            MangaHomeItem.manga_id == manga.id,
                            MangaHomeItem.section_id == section_id
                        ).first()
                        if not existing_home_item:
                            home_item = MangaHomeItem(
                                manga_id=manga.id,
                                section_id=section_id,
                                position=position,
                                chapter_number=chapter_number if section_name in ["ultimas_subidas", "ultimos_anadidos"] else None,
                                upload_time=upload_time if section_name in ["ultimas_subidas", "ultimos_anadidos"] else None,
                                created_at=created_at
                            )
                            db.add(home_item)
                            db.flush()  # Flush en lugar de commit para mantener la transacción abierta
                            print(f"Agregado a manga_home_items ({section_name}): {manga.id}")
                        else:
                            existing_home_item.position = position
                            if section_name in ["ultimas_subidas", "ultimos_anadidos"]:
                                existing_home_item.chapter_number = chapter_number if chapter_number is not None else existing_home_item.chapter_number
                                existing_home_item.upload_time = upload_time if upload_time else existing_home_item.upload_time
                            db.flush()  # Flush para actualizar
                            print(f"Actualizado en manga_home_items ({section_name}): {manga.id}")

                    except IntegrityError as ie:
                        db.rollback()
                        print(f"Error de integridad procesando {title} en {section_name}: {str(ie)}")
                        continue
                    except Exception as e:
                        db.rollback()
                        print(f"Error procesando {title} en {section_name}: {str(e)}")
                        continue

        db.commit()
        print("Datos de manga home procesados y guardados correctamente.")
        
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
        "publishing": MediaStatus.publishing,
        "ended": MediaStatus.finished,
        "finished": MediaStatus.finished,
        "cancelled": MediaStatus.canceled,
        "paused": MediaStatus.paused,
        "on_hold": MediaStatus.paused
    }
    translation_status_map = {
        "active": TranslationStatus.active,
        "finished": TranslationStatus.finished,
        "abandoned": TranslationStatus.abandoned
    }
    yes_no_map = {
        "yes": YesNoEnum.yes,
        "no": YesNoEnum.no
    }
    
    try:
        print("Procesando resultados de búsqueda de mangas...")
        
        def get_or_create_category(manga_type: str):
            type_to_slug = {
                "manga": "manga",
                "manhua": "manhua",
                "manhwa": "manhwa",
                "novel": "novel",
                "one shot": "one_shot",
                "doujinshi": "doujinshi",
                "oel": "oel"
            }
            slug = type_to_slug.get(manga_type.lower(), "manga")
            category = db.query(MediaType).filter(
                MediaType.slug == slug,
                MediaType.media_type == MediaTypeEnum.manga
            ).first()
            if not category:
                category = MediaType(
                    name=manga_type.capitalize(),
                    slug=slug,
                    media_type=MediaTypeEnum.manga
                )
                db.add(category)
                db.flush()
                print(f"Categoría creada: {category.id} - {category.name}")
            return category

        for item in data.get("results", []):
            try:
                print(f"Procesando manga {item.get('title', 'N/A')}")
                
                # Extraer ID
                media_id_match = re.search(r'/(\d+)/', item.get("url", ""))
                media_id = int(media_id_match.group(1)) if media_id_match else None
                
                # Category
                category = get_or_create_category(item.get("type", "manga"))
                
                # Buscar o crear Manga
                media = db.query(Media).filter(Media.id == media_id).first() if media_id else None
                
                if not media:
                    media = Media(
                        id=media_id,
                        title=item["title"],
                        slug=generate_slug(item["title"]),
                        subtitle=item.get("subtitle"),
                        description=item.get("description"),
                        cover_url=item.get("cover_url") or item.get("image_url"),
                        type=item.get("type", "manga"),
                        demography=item.get("demography", "") if item.get("demography") != "unknown" else "",
                        state=item.get("state", ""),
                        status=status_map.get(item.get("status", "").lower(), MediaStatus.publishing),
                        translation_status=translation_status_map.get(item.get("translation_status", "").lower(), TranslationStatus.active),
                        webcomic=yes_no_map.get(item.get("webcomic", "no"), YesNoEnum.no),
                        yonkoma=yes_no_map.get(item.get("yonkoma", "no"), YesNoEnum.no),
                        amateur=yes_no_map.get(item.get("amateur", "no"), YesNoEnum.no),
                        erotic=yes_no_map.get(item.get("is_erotic", "no"), YesNoEnum.no),
                        score=float(item["score"]) if item.get("score") and item["score"] != "Unknown" else None,
                        popularity=item.get("popularity", 0),
                        url=item.get("url"),
                        alt_titles=item.get("alt_titles", []),
                        synonyms=item.get("synonyms", []),
                        category_id=category.id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.flush()
                    print(f"Manga creado: {media.id} - {media.title}")
                else:
                    media.title = item.get("title", media.title)
                    media.slug = generate_slug(item["title"]) if not media.slug else media.slug
                    media.subtitle = item.get("subtitle", media.subtitle)
                    media.description = item.get("description", media.description)
                    media.cover_url = (item.get("cover_url") or item.get("image_url") or media.cover_url) if item.get("cover_url") != "Unknown" else media.cover_url
                    media.type = item.get("type", media.type)
                    media.demography = item.get("demography", media.demography) if item.get("demography") != "unknown" else media.demography
                    media.state = item.get("state", media.state)
                    media.status = status_map.get(item.get("status", "").lower(), media.status)
                    media.translation_status = translation_status_map.get(item.get("translation_status", "").lower(), media.translation_status)
                    media.webcomic = yes_no_map.get(item.get("webcomic", media.webcomic.value), media.webcomic)
                    media.yonkoma = yes_no_map.get(item.get("yonkoma", media.yonkoma.value), media.yonkoma)
                    media.amateur = yes_no_map.get(item.get("amateur", media.amateur.value), media.amateur)
                    media.erotic = yes_no_map.get(item.get("is_erotic", media.erotic.value), media.erotic)
                    media.score = float(item["score"]) if item.get("score") and item["score"] != "Unknown" else media.score
                    media.popularity = item.get("popularity", media.popularity)
                    media.url = item.get("url", media.url)
                    media.alt_titles = item.get("alt_titles", media.alt_titles)
                    media.synonyms = item.get("synonyms", media.synonyms)
                    media.category_id = category.id
                    media.updated_at = datetime.utcnow()
                
                # Procesar géneros
                genre_slugs = []
                for g in item.get("genres", []):
                    if isinstance(g, dict):
                        g_slug = g.get("slug") or generate_slug(g.get("name", ""))
                        g_name = g.get("name", "")
                    else:
                        g_slug = generate_slug(g)
                        g_name = g
                    if g_slug.lower() != "unknown":
                        genre_slugs.append((g_slug, g_name))
                
                existing_genres = []
                for g_slug, g_name in genre_slugs:
                    genre = db.query(Genre).filter(Genre.slug == g_slug).first()
                    if not genre:
                        genre = Genre(
                            name=g_name,
                            slug=g_slug,
                            applies_to=["manga"]
                        )
                        db.add(genre)
                        db.flush()
                        print(f"Género creado: {genre.id} - {genre.name}")
                    existing_genres.append(genre)
                
                media.genres = existing_genres
                db.commit()

            except IntegrityError as ie:
                db.rollback()
                print(f"Error de integridad procesando {item.get('title', 'N/A')}: {str(ie)}")
                continue
            except Exception as e:
                db.rollback()
                print(f"Error procesando {item.get('title', 'N/A')}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

        db.commit()
        print("Todos los datos de búsqueda de mangas procesados y guardados correctamente.")
        
    except Exception as e:
        db.rollback()
        print(f"Error general en save_manga_search: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

# Función para guardar Manga Filters
def save_manga_filters(data: dict):
    """
    Guarda las opciones de filtros de mangas en la tabla MangaFilterOption.
    
    Args:
        data (dict): Diccionario con los filtros y sus opciones, como el retornado por el endpoint /filters.
    """
    db = next(get_db())
    try:
        print("Procesando filtros de mangas...")
        for filter_name, filter_info in data.get("filters", {}).items():
            try:
                values = filter_info.get("values", [])
                if not values and filter_name == "title":
                    continue  # Texto libre
                for value in values:
                    try:
                        option = db.query(FilterOption).filter(
                            FilterOption.filter_name == filter_name,
                            FilterOption.option_value == value
                        ).first()
                        if not option:
                            print(f"Guardando filtro {filter_name}: {value}")
                            option = FilterOption(
                                filter_name=filter_name,
                                option_value=value,
                                option_label=filter_info.get("label", value),
                                option_type=filter_info.get("type", "string"),
                                default_value=filter_info.get("default") if filter_name in ["order_item", "order_dir", "page"] else None,
                                min_value=filter_info.get("min"),
                                max_value=filter_info.get("max")
                            )
                            db.add(option)
                            db.commit()
                        else:
                            print(f"Filtro {filter_name}: {value} ya existe")
                    except IntegrityError:
                        db.rollback()
                        print(f"Filtro {filter_name}: {value} ya existe (conflicto de unicidad)")
                    except Exception as e:
                        db.rollback()
                        print(f"Error al guardar filtro {filter_name}: {value}: {e}")
            except Exception as e:
                print(f"Error procesando filtro {filter_name}: {e}")
                continue
        print("Todos los filtros de mangas procesados y guardados correctamente.")
    except Exception as e:
        db.rollback()
        print(f"Error general al guardar filtros de mangas: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()