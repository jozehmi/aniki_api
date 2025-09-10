from sqlalchemy.exc import IntegrityError
from aniki import AnimeFilterOption as FilterOption, Genre, Anime as Media, Episode, Embed, Download, AnimeStatusEnum as MediaStatus, Category as MediaType, get_db, AnimeHomeFeatured, AnimeHomeLatestEpisode, AnimeHomeLatestMedia, MediaTypeEnum
from datetime import datetime
from dateutil import parser
from slugify import slugify
from sqlalchemy.orm import Session
import re

# Función para guardar Anime Home
def save_anime_home(data: dict):
    # print(f"Datos recibidos en save_anime_home: {data}")
    db = next(get_db())
    status_map = {
        0: MediaStatus.proximamente,
        1: MediaStatus.finalizado,
        2: MediaStatus.emision
    }
    try:
        # Limpiar las tablas home antes de procesar nuevos datos
        # print("Limpiando tablas home...")
        db.query(AnimeHomeFeatured).delete()
        db.query(AnimeHomeLatestEpisode).delete()
        db.query(AnimeHomeLatestMedia).delete()
        db.commit()
        # print("Tablas home limpiadas.")

        # print("Procesando featured...")
        for i, item in enumerate(data.get("featured", [])):
            try:
                # print(f"Procesando media {item['id']}: {item['title']}")
                mt_data = item.get("category")
                if mt_data:
                    media_type = db.query(MediaType).filter(MediaType.name == mt_data["name"]).first()
                    if not media_type:
                        # print(f"Creando media_type {mt_data['name']}")
                        media_type = MediaType(
                            name=mt_data["name"],
                            description=mt_data.get("description", f"Tipo {mt_data['name']}"),
                            added_at=datetime.utcnow()
                        )
                        db.add(media_type)
                        db.commit()

                start_date = parser.parse(item["startDate"]).date() if item.get("startDate") else None
                created_at_featured = parser.isoparse(item["createdAt"]) if item.get("createdAt") else datetime.utcnow()
                media = db.query(Media).filter(Media.id == item["id"]).first()
                if not media:
                    # print(f"Creando media {item['id']}: {item['title']}")
                    media = Media(
                        id=item["id"],
                        slug=item["slug"],
                        title=item["title"],
                        synopsis=item["synopsis"],
                        start_date=start_date,
                        status=status_map.get(item["status"]) if item.get("status") is not None else None,
                        poster_url=item.get("image_url"),
                        watch_url=item.get("watch_url"),
                        category_id=media_type.id if mt_data else None,
                        featured=True,
                        created_at=datetime.utcnow()
                    )
                    db.add(media)
                    db.commit()

                for g in item.get("genres", []):
                    genre = db.query(Genre).filter(Genre.slug == g["slug"]).first()
                    if not genre:
                        # print(f"Creando género {g['name']}: {g['slug']}")
                        genre = Genre(
                            name=g["name"],
                            slug=g["slug"],
                            added_at=datetime.utcnow()
                        )
                        db.add(genre)
                        db.commit()
                    if genre not in media.genres:
                        # print(f"Asociando género {g['slug']} con media {media.id}")
                        media.genres.append(genre)
                        db.commit()

                # Guardar en anime_home_featured
                home_featured = AnimeHomeFeatured(
                    anime_id=media.id,
                    section_id=1,
                    position=i,
                    created_at=created_at_featured
                )
                db.add(home_featured)
                db.commit()
            except Exception as e:
                print(f"Error procesando featured item {item['id']}: {e}")
                db.rollback()
                continue

        print("Procesando latestEpisodes...")
        print(f"Procesando {len(data.get('latestEpisodes', []))} episodios en latestEpisodes")
        for ep in data.get("latestEpisodes", []):
            try:
                print(f"Procesando episodio {ep['id']}, número {ep['number']}")
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
                    # print(f"Creando media {media_data['id']}: {media_data['title']}")
                    media = Media(
                        id=media_data["id"],
                        slug=media_data["slug"],
                        title=media_data["title"],
                        aka_ja_jp=None,
                        synopsis=None,
                        start_date=None,
                        end_date=None,
                        status=None,
                        score=None,
                        votes=None,
                        backdrop_url=None,
                        trailer_id=None,
                        poster_url=None,
                        watch_url=None,
                        seasons=None,
                        episodes_count=None,
                        mal_id=None,
                        mature=False,
                        featured=False,
                        category_id=media_type.id,
                        created_at=datetime.utcnow(),
                        updated_at=None
                    )
                    db.add(media)
                    db.commit()
                # else:
                #     # print(f"Media {media_data['id']} ya existe")

                created_at = parser.isoparse(ep["createdAt"]) if ep.get("createdAt") else datetime.utcnow()
                episode = db.query(Episode).filter(Episode.id == ep["id"]).first()
                if not episode:
                    # print(f"Creando episode {ep['id']} para media {media.id}")
                    episode = Episode(
                        id=ep["id"],
                        anime_id=media.id,
                        number=ep["number"],
                        image_url=ep.get("image_url"),
                        watch_url=ep.get("watch_url"),
                        filler=False,
                        created_at=created_at
                    )
                    db.add(episode)
                    db.commit()
                
                    # print(f"Episodio {ep['id']} ya existe")

                # Guardar en anime_home_latest_episodes
                home_latest_ep = AnimeHomeLatestEpisode(
                    episode_id=episode.id,
                    section_id=2,
                    created_at=created_at
                )
                db.add(home_latest_ep)
                db.commit()
                print(f"Agregado a home_latest_episodes: {episode.id}")
            except Exception as e:
                # print(f"Error procesando episodio {ep['id']}: {e}")
                db.rollback()
                continue

        # print("Procesando latestMedia...")
        for item in data.get("latestMedia", []):
            try:
                # print(f"Procesando media {item['id']}: {item['title']}")
                mt_data = item.get("category")
                if mt_data:
                    media_type = db.query(MediaType).filter(MediaType.name == mt_data["name"]).first()
                    if not media_type:
                        # print(f"Creando media_type {mt_data['name']}")
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
                    # print(f"Creando media {item['id']}: {item['title']}")
                    media = Media(
                        id=item["id"],
                        slug=item["slug"],
                        title=item["title"],
                        synopsis=item.get("synopsis"),
                        poster_url=item.get("image_url"),
                        watch_url=item.get("watch_url"),
                        backdrop_url=item.get("poster"),
                        category_id=media_type.id if mt_data else None,
                        created_at=created_at
                    )
                    db.add(media)
                    db.commit()

                # Guardar en anime_home_latest_media
                home_latest_media = AnimeHomeLatestMedia(
                    media_type=MediaTypeEnum.anime,
                    media_id=media.id,
                    section_id=3,
                    created_at=created_at
                )
                db.add(home_latest_media)
                db.commit()
            except Exception as e:
                # print(f"Error procesando latestMedia item {item['id']}: {e}")
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
                    poster_url=anime.get("cover"),
                    category_id=media_type.id if mt_data else None,
                    created_at=datetime.utcnow()
                )
            db.add(media)
            db.commit()
        else:
            media.synopsis = anime.get("synopsis") or media.synopsis
            media.poster_url = anime.get("cover") or media.poster_url
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
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
                aka_ja_jp=anime_data.get("aka"),
                score=anime_data.get("score"),
                votes=anime_data.get("votes"),
                status=status_enum,
                category_id=media_type.id,
                created_at=datetime.utcnow()
            )
            db.add(media)
        else:
            media.score = anime_data.get("score", media.score)
            media.votes = anime_data.get("votes", media.votes)
            media.status = status_enum or media.status

        for g in anime_data.get("genres", []):
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

        ep_data = data.get("episode")
        episode = db.query(Episode).filter(Episode.id == ep_data["id"]).first()
        if not episode:
            episode_by_key = db.query(Episode).filter(Episode.anime_id == media.id, Episode.number == ep_data["number"]).first()
            image_url = episode_by_key.image_url if episode_by_key else None
            watch_url = episode_by_key.watch_url if episode_by_key else None
            if episode_by_key and episode_by_key.id < 100000:  # Umbral para detectar placeholders
                db.delete(episode_by_key)
                db.commit()
            episode = Episode(
                id=ep_data["id"],
                anime_id=media.id,
                number=ep_data["number"],
                filler=ep_data.get("filler", False),
                image_url=image_url,
                watch_url=watch_url,
                created_at=datetime.utcnow()
            )
            db.add(episode)
        else:
            episode.filler = ep_data.get("filler", episode.filler)
            episode.image_url = ep_data.get("image") or episode.image_url
            episode.watch_url = ep_data.get("url") or episode.watch_url

        for emb in data.get("embeds", []):
            embed = db.query(Embed).filter(Embed.episode_id == episode.id, Embed.server == emb["server"], Embed.url == emb["url"]).first()
            if not embed:
                embed = Embed(
                    episode_id=episode.id,
                    server=emb["server"],
                    url=emb["url"],
                    variant=emb.get("variant"),
                    added_at=datetime.utcnow()
                )
                db.add(embed)

        for dl in data.get("downloads", []):
            download = db.query(Download).filter(Download.episode_id == episode.id, Download.server == dl["server"], Download.url == dl["url"]).first()
            if not download:
                download = Download(
                    episode_id=episode.id,
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
                    category_id=media_type.id if mt_data else None,
                    created_at=created_at
                )
                db.add(media)
                db.commit()

            le_data = item.get("latestEpisode")
            if le_data:
                created_at_ep = parser.isoparse(le_data["createdAt"].replace("+00:00", "")) if le_data.get("createdAt") else datetime.utcnow()
                episode = db.query(Episode).filter(Episode.id == le_data["id"]).first()
                if not episode:
                    episode = Episode(
                        id=le_data["id"],
                        anime_id=media.id,
                        number=le_data["number"],
                        created_at=created_at_ep
                    )
                    db.add(episode)
                    db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error al guardar en la base de datos: {e}")
        raise
    finally:
        db.close()