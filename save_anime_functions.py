from sqlalchemy.exc import IntegrityError
from aniki import AnimeFilterOption as FilterOption, Genre, Anime as Media, Episode, Embed, Download, AnimeStatusEnum as MediaStatus, Category as MediaType, get_db, AnimeHomeFeatured, AnimeHomeLatestEpisode, AnimeHomeLatestMedia, MediaTypeEnum
from datetime import datetime
from dateutil import parser
from slugify import slugify
from sqlalchemy.orm import Session
import re
from sqlalchemy import or_

from datetime import datetime
from dateutil import parser
from sqlalchemy.exc import IntegrityError
from aniki import AnimeFilterOption as FilterOption, Genre, Anime as Media, Episode, Embed, Download, AnimeCatalog, AnimeHomeSection, AnimeStatusEnum as MediaStatus, Category as MediaType, get_db, AnimeHomeFeatured, AnimeHomeLatestEpisode, AnimeHomeLatestMedia, MediaTypeEnum, AnimeSchedule

def save_anime_home(data: dict):
    db = next(get_db())
    status_map = {
        0: MediaStatus.proximamente,
        1: MediaStatus.finalizado,
        2: MediaStatus.emision
    }
    
    try:
        # Limpiar las tablas home
        db.query(AnimeHomeFeatured).delete()
        db.query(AnimeHomeLatestEpisode).delete()
        db.query(AnimeHomeLatestMedia).delete()
        db.commit()

        # Procesar featured
        print("Procesando featured...")
        print(f"Procesando {len(data.get('featured', []))} elementos destacados")
        
        for item in data.get("featured", []):
            try:
                print(f"Procesando anime destacado {item['id']}")
                
                # Buscar o crear la categoría
                category_data = item.get("category")
                category = db.query(MediaType).filter(MediaType.id == category_data["id"]).first()
                if not category:
                    category = MediaType(
                        id=category_data["id"],
                        name=category_data["name"],
                        slug=category_data["name"].lower().replace(" ", "-"),
                        media_type=MediaTypeEnum.anime
                    )
                    db.add(category)
                    db.commit()
                    print(f"Categoría creada: {category.id} - {category.name}")

                # Buscar o crear el anime
                media = db.query(Media).filter(Media.id == item["id"]).first()
                
                if not media:
                    media = Media(
                        id=item["id"],
                        slug=item["slug"],
                        title=item["title"],
                        synopsis=item.get("synopsis"),
                        backdrop_url=item.get("image_url"),
                        watch_url=item.get("watch_url"),
                        status=status_map.get(item.get("status"), MediaStatus.unknown),
                        start_date=parser.isoparse(item["startDate"]) if item.get("startDate") else None,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        category_id=category.id
                    )
                    db.add(media)
                    db.commit()
                    print(f"Media creado: {media.id} - {media.title}")
                else:
                    # Actualizar datos del anime
                    media.slug = item["slug"]
                    media.title = item["title"]
                    media.synopsis = item.get("synopsis")
                    media.backdrop_url = item.get("image_url")
                    media.watch_url = item.get("watch_url")
                    media.status = status_map.get(item.get("status"), MediaStatus.unknown)
                    media.start_date = parser.isoparse(item["startDate"]) if item.get("startDate") else media.start_date
                    media.updated_at = datetime.utcnow()
                    media.category_id = category.id

                # Manejar géneros
                genre_ids = [g["id"] for g in item.get("genres", [])]
                existing_genres = db.query(Genre).filter(Genre.id.in_(genre_ids)).all()
                existing_genre_ids = {g.id for g in existing_genres}
                
                # Crear géneros que no existan
                for genre_data in item.get("genres", []):
                    if genre_data["id"] not in existing_genre_ids:
                        genre = Genre(
                            id=genre_data["id"],
                            name=genre_data["name"],
                            slug=genre_data["slug"],
                            applies_to=["anime"]
                        )
                        db.add(genre)
                        existing_genres.append(genre)
                        print(f"Género creado: {genre.id} - {genre.name}")
                
                db.commit()
                
                # Asociar géneros al anime
                media.genres = existing_genres
                db.commit()

                # Verificar si ya existe en home_featured
                existing_home_featured = db.query(AnimeHomeFeatured).filter(
                    AnimeHomeFeatured.anime_id == media.id
                ).first()

                if not existing_home_featured:
                    home_featured = AnimeHomeFeatured(
                        anime_id=media.id,
                        section_id=1,  # Asumiendo section_id=1 para featured
                        position=item.get("position", 0),
                        created_at=parser.isoparse(item["createdAt"]) if item.get("createdAt") else datetime.utcnow()
                    )
                    db.add(home_featured)
                    db.commit()
                    print(f"Agregado a home_featured: {media.id}")
                else:
                    print(f"Ya existe en home_featured: {media.id}")

            except IntegrityError as ie:
                print(f"Error de integridad procesando anime destacado {item.get('id', 'N/A')}: {str(ie)}")
                db.rollback()
                continue
            except Exception as e:
                print(f"Error procesando anime destacado {item.get('id', 'N/A')}: {str(e)}")
                import traceback
                traceback.print_exc()
                db.rollback()
                continue

        # Procesar latestEpisodes
        print("Procesando latestEpisodes...")
        print(f"Procesando {len(data.get('latestEpisodes', []))} episodios")
        
        for ep in data.get("latestEpisodes", []):
            try:
                print(f"Procesando episodio ID {ep['id']} del anime {ep['media']['id']}")
                
                # Buscar o crear el anime
                media_data = ep.get("media")
                media = db.query(Media).filter(Media.id == media_data["id"]).first()
                
                if not media:
                    media = Media(
                        id=media_data["id"],
                        slug=media_data["slug"],
                        title=media_data["title"],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()
                    print(f"Media creado: {media.id} - {media.title}")

                # Buscar episodio por ID
                episode = db.query(Episode).filter(Episode.id == ep["id"]).first()

                created_at = parser.isoparse(ep["createdAt"]) if ep.get("createdAt") else datetime.utcnow()
                
                if not episode:
                    # Crear nuevo episodio con el ID proporcionado
                    episode = Episode(
                        id=ep["id"],  # Usar el ID del episodio del JSON
                        anime_id=media_data["id"],
                        number=ep["number"],
                        image_url=ep.get("image_url"),
                        watch_url=ep.get("watch_url"),
                        filler=False,
                        created_at=created_at,
                        published_at=parser.isoparse(ep["publishedAt"]) if ep.get("publishedAt") else None
                    )
                    db.add(episode)
                    db.commit()
                    print(f"Episodio creado: ID {episode.id}, número {episode.number} para anime {media.id}")
                else:
                    # Actualizar episodio existente
                    episode.anime_id = media_data["id"]
                    episode.number = ep["number"]
                    episode.image_url = ep.get("image_url")
                    episode.watch_url = ep.get("watch_url")
                    episode.published_at = parser.isoparse(ep["publishedAt"]) if ep.get("publishedAt") else None
                    episode.updated_at = datetime.utcnow()
                    print(f"Episodio actualizado: ID {episode.id}, número {episode.number} para anime {media.id}")

                # Verificar si ya existe en home_latest_episodes
                existing_home_ep = db.query(AnimeHomeLatestEpisode).filter(
                    AnimeHomeLatestEpisode.episode_id == episode.id
                ).first()

                if not existing_home_ep:
                    home_latest_ep = AnimeHomeLatestEpisode(
                        episode_id=episode.id,
                        section_id=2,  # Asumiendo section_id=2 para latestEpisodes
                        created_at=created_at
                    )
                    db.add(home_latest_ep)
                    db.commit()
                    print(f"Agregado a home_latest_episodes: {episode.id}")
                else:
                    print(f"Ya existe en home_latest_episodes: {episode.id}")

            except IntegrityError as ie:
                print(f"Error de integridad procesando episodio ID {ep.get('id', 'N/A')}: {str(ie)}")
                db.rollback()
                continue
            except Exception as e:
                print(f"Error procesando episodio ID {ep.get('id', 'N/A')}: {str(e)}")
                import traceback
                traceback.print_exc()
                db.rollback()
                continue

        # Procesar latestMedia
        print("Procesando latestMedia...")
        print(f"Procesando {len(data.get('latestMedia', []))} medios recientes")
        
        for media_item in data.get("latestMedia", []):
            try:
                print(f"Procesando anime reciente {media_item['id']}")
                
                # Buscar o crear la categoría
                category_data = media_item.get("category")
                category = db.query(MediaType).filter(MediaType.id == category_data["id"]).first()
                if not category:
                    category = MediaType(
                        id=category_data["id"],
                        name=category_data["name"],
                        slug=category_data["name"].lower().replace(" ", "-"),
                        media_type=MediaTypeEnum.anime
                    )
                    db.add(category)
                    db.commit()
                    print(f"Categoría creada: {category.id} - {category.name}")

                # Buscar o crear el anime
                media = db.query(Media).filter(Media.id == media_item["id"]).first()
                
                if not media:
                    media = Media(
                        id=media_item["id"],
                        slug=media_item["slug"],
                        title=media_item["title"],
                        synopsis=media_item.get("synopsis"),
                        poster_url=media_item.get("poster"),
                        backdrop_url=media_item.get("image_url"),
                        watch_url=media_item.get("watch_url"),
                        created_at=parser.isoparse(media_item["createdAt"]) if media_item.get("createdAt") else datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        category_id=category.id
                    )
                    db.add(media)
                    db.commit()
                    print(f"Media creado: {media.id} - {media.title}")
                else:
                    # Actualizar datos del anime
                    media.slug = media_item["slug"]
                    media.title = media_item["title"]
                    media.synopsis = media_item.get("synopsis")
                    media.poster_url = media_item.get("poster")
                    media.backdrop_url = media_item.get("image_url")
                    media.watch_url = media_item.get("watch_url")
                    media.updated_at = datetime.utcnow()
                    media.category_id = category.id

                # Verificar si ya existe en home_latest_media
                existing_home_media = db.query(AnimeHomeLatestMedia).filter(
                    AnimeHomeLatestMedia.media_id == media.id,
                    AnimeHomeLatestMedia.media_type == MediaTypeEnum.anime
                ).first()

                if not existing_home_media:
                    home_latest_media = AnimeHomeLatestMedia(
                        media_type=MediaTypeEnum.anime,
                        media_id=media.id,
                        section_id=3,  # Asumiendo section_id=3 para latestMedia
                        created_at=parser.isoparse(media_item["createdAt"]) if media_item.get("createdAt") else datetime.utcnow()
                    )
                    db.add(home_latest_media)
                    db.commit()
                    print(f"Agregado a home_latest_media: {media.id}")
                else:
                    print(f"Ya existe en home_latest_media: {media.id}")

            except IntegrityError as ie:
                print(f"Error de integridad procesando anime reciente {media_item.get('id', 'N/A')}: {str(ie)}")
                db.rollback()
                continue
            except Exception as e:
                print(f"Error procesando anime reciente {media_item.get('id', 'N/A')}: {str(e)}")
                import traceback
                traceback.print_exc()
                db.rollback()
                continue

        db.commit()
        print("Todos los datos procesados y guardados correctamente.")
        
    except Exception as e:
        db.rollback()
        print(f"Error general en save_anime_home: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

# Función para guardar Anime Catalog
def save_anime_catalog(data: dict):
    db = next(get_db())
    status_map = {
        0: MediaStatus.proximamente,
        1: MediaStatus.finalizado,
        2: MediaStatus.emision
    }
    
    try:
        # Obtener la sección "catalog" de AnimeHomeSection
        section = db.query(AnimeHomeSection).filter(AnimeHomeSection.name == "catalog").first()
        if not section:
            raise ValueError("La sección 'catalog' no está definida en AnimeHomeSection")

        for anime in data.get("animes", []):
            # Obtener o crear la categoría
            category_data = anime.get("category")
            category = None
            if category_data:
                category = db.query(MediaType).filter(MediaType.id == category_data["id"]).first()
                if not category:
                    category = MediaType(
                        id=category_data["id"],
                        name=category_data["name"],
                        slug=category_data.get("slug", category_data["name"].lower().replace(" ", "-")),
                        media_type=MediaTypeEnum.anime
                    )
                    db.add(category)
                    db.commit()
                    print(f"Categoría creada: {category.id} - {category.name}")

            # Verificar si el anime ya existe por su id
            anime_record = db.query(Media).filter(Media.id == anime["id"]).first()
            if not anime_record:
                # Crear nuevo registro en la tabla Anime (Media)
                anime_record = Media(
                    id=anime.get("id"),
                    title=anime["title"],
                    slug=anime["slug"],
                    synopsis=anime.get("synopsis"),
                    poster_url=anime.get("cover"),
                    category_id=category.id if category else None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    status=status_map.get(anime.get("status"), MediaStatus.unknown),
                    score=anime.get("score"),
                    votes=anime.get("votes"),
                    episodes_count=anime.get("episodes_count"),
                    start_date=parser.isoparse(anime["startDate"]) if anime.get("startDate") else None,
                    end_date=parser.isoparse(anime["endDate"]) if anime.get("endDate") else None,
                    mal_id=anime.get("mal_id"),
                    seasons=anime.get("seasons"),
                    backdrop_url=anime.get("backdrop_url"),
                    trailer_id=anime.get("trailer_id"),
                    watch_url=anime.get("watch_url"),
                    runtime=anime.get("runtime"),
                    next_date=parser.isoparse(anime["next_date"]) if anime.get("next_date") else None,
                    wait_days=anime.get("wait_days"),
                    featured=anime.get("featured", False),
                    mature=anime.get("mature", False)
                )
                db.add(anime_record)
                db.commit()
                print(f"Media creado: {anime_record.id} - {anime_record.title}")
            else:
                # Actualizar datos si es necesario
                anime_record.synopsis = anime.get("synopsis") or anime_record.synopsis
                anime_record.poster_url = anime.get("cover") or anime_record.poster_url
                anime_record.updated_at = datetime.utcnow()
                anime_record.status = status_map.get(anime.get("status"), anime_record.status)
                anime_record.start_date = parser.isoparse(anime["startDate"]) if anime.get("startDate") else anime_record.start_date
                anime_record.end_date = parser.isoparse(anime["endDate"]) if anime.get("endDate") else anime_record.end_date
                anime_record.category_id = category.id if category else anime_record.category_id
                db.commit()
                print(f"Media actualizado: {anime_record.id} - {anime_record.title}")

            # Manejar géneros
            genre_ids = [g["id"] for g in anime.get("genres", [])]
            existing_genres = db.query(Genre).filter(Genre.id.in_(genre_ids)).all()
            existing_genre_ids = {g.id for g in existing_genres}
            
            # Crear géneros que no existan
            for genre_data in anime.get("genres", []):
                if genre_data["id"] not in existing_genre_ids:
                    genre = Genre(
                        id=genre_data["id"],
                        name=genre_data["name"],
                        slug=genre_data["slug"],
                        applies_to=["anime"]
                    )
                    db.add(genre)
                    existing_genres.append(genre)
                    print(f"Género creado: {genre.id} - {genre.name}")
            
            db.commit()
            
            # Asociar géneros al anime
            anime_record.genres = existing_genres
            db.commit()

            # Añadir el anime a la tabla AnimeCatalog
            catalog_entry = db.query(AnimeCatalog).filter(
                AnimeCatalog.anime_id == anime_record.id,
                AnimeCatalog.section_id == section.id
            ).first()
            if not catalog_entry:
                catalog_entry = AnimeCatalog(
                    anime_id=anime_record.id,
                    section_id=section.id,
                    position=anime.get("position"),
                    created_at=parser.isoparse(anime["createdAt"]) if anime.get("createdAt") else datetime.utcnow()
                )
                db.add(catalog_entry)
                db.commit()
                print(f"Agregado a anime_catalog: {anime_record.id}")
            else:
                print(f"Ya existe en anime_catalog: {anime_record.id}")

    except IntegrityError as e:
        db.rollback()
        print(f"Error de integridad al guardar anime: {e}")
    except Exception as e:
        db.rollback()
        print(f"Error al guardar anime: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

# Función para guardar Anime Details
def save_anime_details(data: dict):
    status_map = {
        1: MediaStatus.emision,
        2: MediaStatus.finalizado,
        3: MediaStatus.proximamente
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
                aka_ja_jp=data.get("aka"),
                synopsis=data.get("synopsis"),
                start_date=start_date,
                end_date=end_date,
                status=status_enum,
                score=data.get("score"),
                votes=data.get("votes"),
                backdrop_url=data.get("backdrop"),
                trailer_id=data.get("trailer"),
                poster_url=data.get("poster"),
                watch_url=data.get("watch_url"),
                seasons=data.get("seasons"),
                episodes_count=data.get("episodes_count"),
                mal_id=data.get("mal_id"),
                mature=data.get("mature", False),
                featured=data.get("featured", False),
                category_id=media_type.id if mt_data else None,
                created_at=created_at,
                updated_at=updated_at
            )
            db.add(media)
        else:
            media.aka_ja_jp = data.get("aka", media.aka_ja_jp)
            media.synopsis = data.get("synopsis", media.synopsis)
            media.start_date = start_date or media.start_date
            media.end_date = end_date or media.end_date
            media.status = status_enum or media.status
            media.score = data.get("score", media.score)
            media.votes = data.get("votes", media.votes)
            media.backdrop_url = data.get("backdrop", media.backdrop_url)
            media.trailer_id = data.get("trailer", media.trailer_id)
            media.poster_url = data.get("poster", media.poster_url)
            media.watch_url = data.get("watch_url", media.watch_url)
            media.seasons = data.get("seasons", media.seasons)
            media.episodes_count = data.get("episodes_count", media.episodes_count)
            media.mal_id = data.get("mal_id", media.mal_id)
            media.mature = data.get("mature", media.mature)
            media.featured = data.get("featured", media.featured)
            media.updated_at = updated_at or media.updated_at

        # Procesar géneros
        for g in data.get("genres", []):
            try:
                genre = db.query(Genre).filter(Genre.slug == g["slug"]).first()
                if not genre:
                    genre = Genre(
                        name=g["name"],
                        slug=g["slug"],
                        added_at=datetime.utcnow()
                    )
                    db.add(genre)
                    db.commit()
                if genre not in media.genres:
                    media.genres.append(genre)
                    db.commit()
            except Exception as e:
                print(f"Error procesando género {g['slug']}: {e}")
                db.rollback()
                continue



        # Procesar content_units (episodios)
        print(f"Procesando {len(data.get('episodes', []))} episodios para media {media.id}")
        for ep in data.get("episodes", []):
            try:
                ep_id = ep.get("id")
                print(f"Procesando episodio número {ep['number']}, id: {ep_id}")
                if ep_id is None:
                    print(f"Saltando episodio {ep['number']} porque id es None")
                    continue
                episode = db.query(Episode).filter(Episode.id == ep_id).first()
                if not episode:
                    episode = db.query(Episode).filter(Episode.anime_id == media.id, Episode.number == ep["number"]).first()
                    if episode:
                        print(f"Encontrado episodio existente por anime_id y number: {episode.id}")
                    else:
                        print(f"No encontrado, creando nuevo episodio")
                if not episode:
                    episode = Episode(
                        id=ep_id,
                        anime_id=media.id,
                        number=ep["number"],
                        image_url=ep.get("image"),
                        watch_url=ep.get("url"),
                        filler=ep.get("filler", False),
                        created_at=datetime.utcnow()
                    )
                    db.add(episode)
                    print(f"Episodio creado: {episode.id}")
                else:
                    print(f"Actualizando episodio existente: {episode.id}")
                    episode.image_url = ep.get("image") or episode.image_url
                    episode.watch_url = ep.get("url") or episode.watch_url
                    episode.filler = ep.get("filler", episode.filler)
                db.commit()
                print(f"Episodio {ep['number']} procesado correctamente")
            except Exception as e:
                print(f"Error procesando episodio {ep.get('number', 'desconocido')}: {e}")
                db.rollback()
                continue
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

# Función para guardar Anime Episode
def save_anime_episode(data: dict):
    status_map = {
        1: MediaStatus.emision,
        2: MediaStatus.finalizado,
        3: MediaStatus.proximamente
    }
    db = next(get_db())
    try:
        anime_data = data.get("anime")
        if not anime_data:
            raise ValueError("Falta la información del anime en 'anime'")

        # Buscar categoría (fallback: TV Anime)
        mt_name = anime_data.get("category", {}).get("name", "TV Anime")
        category = db.query(MediaType).filter(MediaType.name == mt_name).first()
        if not category:
            category = MediaType(
                name=mt_name,
                slug=generate_slug(mt_name),
                media_type=MediaTypeEnum.anime
            )
            db.add(category)
            db.commit()

        # Mapear status
        status_val = anime_data.get("status")
        status_enum = status_map.get(status_val) if isinstance(status_val, int) else MediaStatus(status_val) if status_val else MediaStatus.unknown

        # Buscar o crear Anime
        media = db.query(Media).filter(Media.id == anime_data["id"]).first()
        if not media:
            media = Media(
                id=anime_data["id"],
                title=anime_data["title"],
                slug=generate_slug(anime_data["title"]),
                aka_ja_jp=anime_data.get("aka"),
                score=anime_data.get("score"),
                votes=anime_data.get("votes"),
                status=status_enum,
                episodes_count=anime_data.get("episodes_count"),
                mal_id=anime_data.get("malId"),
                category_id=category.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(media)
        else:
            media.title = anime_data["title"]
            media.slug = media.slug or generate_slug(anime_data["title"])
            media.score = anime_data.get("score", media.score)
            media.votes = anime_data.get("votes", media.votes)
            media.status = status_enum or media.status
            media.episodes_count = anime_data.get("episodes_count", media.episodes_count)
            media.mal_id = anime_data.get("malId", media.mal_id)
            media.updated_at = datetime.utcnow()

        # Manejar géneros (pueden venir como string o dict)
        for g in anime_data.get("genres", []):
            if isinstance(g, str):
                name = g
                slug_val = generate_slug(g)
            elif isinstance(g, dict):
                name = g.get("name")
                slug_val = g.get("slug") or generate_slug(name)
            else:
                continue

            # Buscar por slug o nombre (para evitar duplicados con acentos)
            genre = db.query(Genre).filter(
                or_(Genre.slug == slug_val, Genre.name == name)
            ).first()

            if not genre:
                genre = Genre(
                    name=name,
                    slug=slug_val,
                    applies_to=["anime"]
                )
                db.add(genre)
                db.commit()

            if genre not in media.genres:
                media.genres.append(genre)

        # Procesar episodio
        ep_data = data.get("episode")
        if not ep_data:
            raise ValueError("Falta la información del episodio en 'episode'")

        # Buscar episodio por ID o por (anime_id, number)
        episode = db.query(Episode).filter(Episode.id == ep_data["id"]).first()
        if not episode:
            episode = db.query(Episode).filter(
                Episode.anime_id == media.id,
                Episode.number == ep_data["number"]
            ).first()

        if not episode:
            episode = Episode(
                id=ep_data["id"],
                anime_id=media.id,
                number=ep_data["number"],
                filler=ep_data.get("filler", False),
                image_url=ep_data.get("image"),
                watch_url=ep_data.get("url"),
                created_at=datetime.utcnow(),
                published_at=parser.isoparse(ep_data["publishedAt"]) if ep_data.get("publishedAt") else None
            )
            db.add(episode)
        else:
            episode.filler = ep_data.get("filler", episode.filler)
            episode.image_url = ep_data.get("image") or episode.image_url
            episode.watch_url = ep_data.get("url") or episode.watch_url
            episode.published_at = parser.isoparse(ep_data["publishedAt"]) if ep_data.get("publishedAt") else episode.published_at

        # Procesar embeds
        for emb in data.get("embeds", []):
            embed = db.query(Embed).filter(
                Embed.episode_id == episode.id,
                Embed.server == emb["server"],
                Embed.url == emb["url"]
            ).first()
            if not embed:
                embed = Embed(
                    episode_id=episode.id,
                    server=emb["server"],
                    url=emb["url"],
                    variant=emb.get("variant")
                )
                db.add(embed)

        # Procesar downloads
        for dl in data.get("downloads", []):
            download = db.query(Download).filter(
                Download.episode_id == episode.id,
                Download.server == dl["server"],
                Download.url == dl["url"]
            ).first()
            if not download:
                download = Download(
                    episode_id=episode.id,
                    server=dl["server"],
                    url=dl["url"],
                    variant=dl.get("variant")
                )
                db.add(download)

        db.commit()
        print(f"Episodio {episode.number} del anime {media.title} guardado correctamente.")

    except Exception as e:
        db.rollback()
        print(f"Error en save_anime_episode: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()

# Función auxiliar para generar un slug
def generate_slug(name: str) -> str:
    """Convierte un nombre en un slug (minúsculas, sin espacios, solo caracteres alfanuméricos y guiones)."""
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower()).replace(' ', '-')
    return slug or 'default-slug'  # Fallback si el nombre está vacío

# Función para guardar Anime Schedule
from sqlalchemy import or_

def save_anime_schedule(data: dict):
    db = next(get_db())
    try:
        for item in data.get("schedule", []):
            # --- Categoría ---
            media_type = None
            mt_data = item.get("category")
            if mt_data:
                media_type = db.query(MediaType).filter(
                    or_(
                        MediaType.slug == (mt_data.get("slug") or generate_slug(mt_data["name"])),
                        MediaType.name == mt_data["name"]
                    )
                ).first()
                if not media_type:
                    media_type = MediaType(
                        name=mt_data["name"],
                        slug=mt_data.get("slug") or generate_slug(mt_data["name"]),
                        description=mt_data.get("description", f"Tipo {mt_data['name']}"),
                        media_type=MediaTypeEnum.anime,
                        added_at=datetime.utcnow()
                    )
                    db.add(media_type)
                    db.flush()

            # --- Media ---
            start_date = parser.isoparse(item["startDate"]).date() if item.get("startDate") else None
            created_at = parser.isoparse(item["createdAt"]) if item.get("createdAt") else datetime.utcnow()

            media = db.query(Media).filter(Media.id == item["id"]).first()
            if not media:
                media = Media(
                    id=item["id"],
                    slug=item["slug"],
                    title=item["title"],
                    synopsis=item.get("synopsis"),
                    start_date=start_date,
                    poster_url=item.get("poster"),
                    category_id=media_type.id if media_type else None,
                    created_at=created_at,
                    updated_at=datetime.utcnow(),
                )
                db.add(media)
                db.flush()
            else:
                media.slug = media.slug or item["slug"]
                media.title = item.get("title", media.title)
                media.synopsis = item.get("synopsis", media.synopsis)
                media.start_date = start_date or media.start_date
                media.poster_url = item.get("poster", media.poster_url)
                media.category_id = media_type.id if media_type else media.category_id
                media.updated_at = datetime.utcnow()

            # --- Último episodio ---
            le_data = item.get("latestEpisode")
            latest_ep_id = None
            if le_data:
                created_at_ep = parser.isoparse(le_data["createdAt"]) if le_data.get("createdAt") else datetime.utcnow()
                episode = db.query(Episode).filter(Episode.id == le_data["id"]).first()
                if not episode:
                    episode = Episode(
                        id=le_data["id"],
                        anime_id=media.id,
                        number=le_data["number"],
                        created_at=created_at_ep
                    )
                    db.add(episode)
                    db.flush()
                latest_ep_id = episode.id

            # --- AnimeSchedule ---
            if item.get("day") and item.get("time"):
                schedule_entry = db.query(AnimeSchedule).filter(
                    AnimeSchedule.anime_id == media.id
                ).first()

                if not schedule_entry:
                    schedule_entry = AnimeSchedule(
                        anime_id=media.id,
                        day=item["day"],
                        time=item["time"],
                        latest_episode_id=latest_ep_id
                    )
                    db.add(schedule_entry)
                else:
                    schedule_entry.day = item["day"]
                    schedule_entry.time = item["time"]
                    schedule_entry.latest_episode_id = latest_ep_id or schedule_entry.latest_episode_id

        db.commit()
        print("Horarios guardados/actualizados correctamente.")

    except Exception as e:
        db.rollback()
        print(f"Error al guardar en la base de datos: {e}")
        import traceback; traceback.print_exc()
        raise
    finally:
        db.close()
