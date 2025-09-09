from sqlalchemy import create_engine, Column, Integer, String, Date, Text, DateTime, ForeignKey, Boolean, Float, JSON, Enum, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from enum import Enum as PythonEnum
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.azawidatlmzzpbhrrdjv:[YOUR-PASSWORD]@aws-1-us-east-2.pooler.supabase.com:6543/postgres")
print(f"URL utilizada: {DATABASE_URL}")
ENGINE = create_engine(DATABASE_URL, echo=True)  # echo=True para logs de debug
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)

# Enums
class MediaStatus(PythonEnum):
    EMISION = "emision"
    FINALIZADO = "finalizado"
    PROXIMAMENTE = "proximamente"
    CANCELADO = "cancelado"
    PAUSADO = "pausado"
    PUBLISHING = "publishing"  # Para manga
    FINISHED = "finished"      # Para manga
    ABANDONED = "abandoned"    # Para traducción

class MediaOrder(PythonEnum):
    PREDETERMINADO = "predeterminado"
    POPULAR = "popular"
    SCORE = "score"
    TITLE = "title"
    LATEST_ADDED = "latest_added"
    LATEST_RELEASED = "latest_released"
    LIKES_COUNT = "likes_count"
    CHAPTERS_COUNT = "chapters_count"

class ContentType(PythonEnum):
    EPISODE = "episode"
    CHAPTER = "chapter"

class MediaCategory(PythonEnum):
    TV_ANIME = "tv-anime"
    PELICULA = "pelicula"
    OVA = "ova"
    ESPECIAL = "especial"
    MANGA = "manga"
    MANHWA = "manhwa"
    MANHUA = "manhua"
    NOVEL = "novel"
    ONE_SHOT = "one_shot"
    DOUJINSHI = "doujinshi"
    OEL = "oel"

class Demography(PythonEnum):
    SEINEN = "seinen"
    SHOUJO = "shoujo"
    SHOUNEN = "shounen"
    JOSEI = "josei"
    KODOMO = "kodomo"

# Tabla para tipos de media
class MediaType(Base):
    __tablename__ = "media_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(MediaCategory), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)

# Tabla para géneros
class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)

# Tabla para tags (etiquetas específicas más allá de géneros)
class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)

# Tabla para demografías
class DemographyType(Base):
    __tablename__ = "demography_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(Demography), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)

# Tabla para filtros estáticos (e.g., webcomic, yonkoma, erotic)
class FilterOption(Base):
    __tablename__ = "filter_options"
    id = Column(Integer, primary_key=True, index=True)
    filter_type = Column(String(50), nullable=False, index=True)  # e.g., 'webcomic', 'yonkoma'
    value = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint('filter_type', 'value', name='uix_filter_type_value'),)

# Tabla principal para Media
class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(200), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    alternative_titles = Column(JSON, nullable=True)
    synopsis = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(Enum(MediaStatus), nullable=True)
    translation_status = Column(Enum(MediaStatus), nullable=True)  # Para manga
    score = Column(Float, nullable=True)
    votes = Column(Integer, nullable=True)
    likes_count = Column(Integer, nullable=True)  # Para manga
    image_url = Column(String(500), nullable=True)
    backdrop_url = Column(String(500), nullable=True)
    trailer_url = Column(String(500), nullable=True)
    watch_url = Column(String(500), nullable=True)  # Para anime
    source_url = Column(String(500), nullable=True)  # Para manga
    mature = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    webcomic = Column(Boolean, default=False)
    yonkoma = Column(Boolean, default=False)
    amateur = Column(Boolean, default=False)
    seasons = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    media_type_id = Column(Integer, ForeignKey("media_types.id"), nullable=False)
    demography_id = Column(Integer, ForeignKey("demography_types.id"), nullable=True)

    media_type = relationship("MediaType")
    demography = relationship("DemographyType")
    genres = relationship("MediaGenre", back_populates="media")
    tags = relationship("MediaTag", back_populates="media")
    content_units = relationship("ContentUnit", back_populates="media")

# Relación muchos-a-muchos para géneros
class MediaGenre(Base):
    __tablename__ = "media_genres"
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)
    genre_id = Column(Integer, ForeignKey("genres.id"), nullable=False)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint('media_id', 'genre_id', name='uix_media_genre'),)
    media = relationship("Media", back_populates="genres")
    genre = relationship("Genre")

# Relación muchos-a-muchos para tags
class MediaTag(Base):
    __tablename__ = "media_tags"
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint('media_id', 'tag_id', name='uix_media_tag'),)
    media = relationship("Media", back_populates="tags")
    tag = relationship("Tag")

# Tabla para episodios/capítulos
class ContentUnit(Base):
    __tablename__ = "content_units"
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)
    type = Column(Enum(ContentType), nullable=False)
    number = Column(Float, nullable=False)  # Soporta capítulos .5
    title = Column(String(200), nullable=True)
    synopsis = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    image_url = Column(String(500), nullable=True)
    url = Column(String(500), nullable=True)
    group_name = Column(String(100), nullable=True)  # Para grupos de traducción
    is_filler = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    media = relationship("Media", back_populates="content_units")
    embeds = relationship("Embed", back_populates="content_unit")
    downloads = relationship("Download", back_populates="content_unit")

# Tabla para embeds
class Embed(Base):
    __tablename__ = "embeds"
    id = Column(Integer, primary_key=True, index=True)
    content_unit_id = Column(Integer, ForeignKey("content_units.id"), nullable=False)
    server = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    variant = Column(String(50), nullable=True)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    content_unit = relationship("ContentUnit", back_populates="embeds")

# Tabla para descargas
class Download(Base):
    __tablename__ = "downloads"
    id = Column(Integer, primary_key=True, index=True)
    content_unit_id = Column(Integer, ForeignKey("content_units.id"), nullable=False)
    server = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    variant = Column(String(50), nullable=True)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    content_unit = relationship("ContentUnit", back_populates="downloads")

# Función para inicializar datos estáticos
def initialize_static_data(db):
    # Media Types
    media_types = [
        {'name': MediaCategory.TV_ANIME, 'description': 'Series de anime transmitidas en TV'},
        {'name': MediaCategory.PELICULA, 'description': 'Películas de anime'},
        {'name': MediaCategory.OVA, 'description': 'Original Video Animation'},
        {'name': MediaCategory.ESPECIAL, 'description': 'Episodios especiales de anime'},
        {'name': MediaCategory.MANGA, 'description': 'Cómics japoneses'},
        {'name': MediaCategory.MANHWA, 'description': 'Cómics coreanos'},
        {'name': MediaCategory.MANHUA, 'description': 'Cómics chinos'},
        {'name': MediaCategory.NOVEL, 'description': 'Novelas ligeras'},
        {'name': MediaCategory.ONE_SHOT, 'description': 'Historias de un solo capítulo'},
        {'name': MediaCategory.DOUJINSHI, 'description': 'Obras autoeditadas, usualmente fan-made'},
        {'name': MediaCategory.OEL, 'description': 'Original English Language manga'},
    ]
    for mt in media_types:
        existing = db.query(MediaType).filter_by(name=mt['name']).first()
        if not existing:
            db.add(MediaType(**mt))

    # Demografías
    demographies = [
        {'name': Demography.SEINEN, 'description': 'Dirigido a hombres adultos'},
        {'name': Demography.SHOUJO, 'description': 'Dirigido a chicas jóvenes'},
        {'name': Demography.SHOUNEN, 'description': 'Dirigido a chicos jóvenes'},
        {'name': Demography.JOSEI, 'description': 'Dirigido a mujeres adultas'},
        {'name': Demography.KODOMO, 'description': 'Dirigido a niños'},
    ]
    for demo in demographies:
        existing = db.query(DemographyType).filter_by(name=demo['name']).first()
        if not existing:
            db.add(DemographyType(**demo))

    # Géneros (unificados para anime y manga)
    genres = [
        {'name': 'Acción', 'slug': 'accion'},
        {'name': 'Aventura', 'slug': 'aventura'},
        {'name': 'Comedia', 'slug': 'comedia'},
        {'name': 'Drama', 'slug': 'drama'},
        {'name': 'Fantasía', 'slug': 'fantasia'},
        {'name': 'Misterio', 'slug': 'misterio'},
        {'name': 'Romance', 'slug': 'romance'},
        {'name': 'Sobrenatural', 'slug': 'sobrenatural'},
        {'name': 'Shounen', 'slug': 'shounen'},
        {'name': 'Seinen', 'slug': 'seinen'},
        {'name': 'Shoujo', 'slug': 'shoujo'},
        {'name': 'Ciencia Ficción', 'slug': 'ciencia-ficcion'},
        {'name': 'Deportes', 'slug': 'deportes'},
        {'name': 'Recuentos de la Vida', 'slug': 'recuentos-de-la-vida'},
        {'name': 'Suspenso', 'slug': 'suspenso'},
        {'name': 'Terror', 'slug': 'terror'},
        {'name': 'Ecchi', 'slug': 'ecchi'},
        {'name': 'Harem', 'slug': 'harem'},
        {'name': 'Mecha', 'slug': 'mecha'},
        {'name': 'Psicológico', 'slug': 'psychological'},
        {'name': 'Girls Love', 'slug': 'girls_love'},
        {'name': 'Boys Love', 'slug': 'boys_love'},
        {'name': 'Supervivencia', 'slug': 'survival'},
        {'name': 'Reencarnación', 'slug': 'reincarnation'},
        {'name': 'Gore', 'slug': 'gore'},
        {'name': 'Apocalíptico', 'slug': 'apocalyptic'},
        {'name': 'Tragedia', 'slug': 'tragedy'},
        {'name': 'Vida Escolar', 'slug': 'school_life'},
        {'name': 'Historia', 'slug': 'history'},
        {'name': 'Militar', 'slug': 'military'},
        {'name': 'Policía', 'slug': 'police'},
        {'name': 'Crimen', 'slug': 'crime'},
        {'name': 'Superpoderes', 'slug': 'super_powers'},
        {'name': 'Vampiros', 'slug': 'vampires'},
        {'name': 'Artes Marciales', 'slug': 'martial_arts'},
        {'name': 'Samurái', 'slug': 'samurai'},
        {'name': 'Género Bender', 'slug': 'gender_bender'},
        {'name': 'Realidad Virtual', 'slug': 'virtual_reality'},
        {'name': 'Cyberpunk', 'slug': 'cyberpunk'},
        {'name': 'Música', 'slug': 'music'},
        {'name': 'Parodia', 'slug': 'parody'},
        {'name': 'Animación', 'slug': 'animation'},
        {'name': 'Demonios', 'slug': 'demons'},
        {'name': 'Familia', 'slug': 'family'},
        {'name': 'Extranjero', 'slug': 'foreign'},
        {'name': 'Niños', 'slug': 'kids'},
        {'name': 'Realidad', 'slug': 'reality'},
        {'name': 'Telenovela', 'slug': 'soap_opera'},
        {'name': 'Guerra', 'slug': 'war'},
        {'name': 'Western', 'slug': 'western'},
        {'name': 'Trampas', 'slug': 'traps'},
    ]
    for genre in genres:
        existing = db.query(Genre).filter_by(name=genre['name']).first()
        if not existing:
            db.add(Genre(**genre))

    # Tags (ejemplos de etiquetas específicas)
    tags = [
        {'name': 'Isekai', 'slug': 'isekai'},
        {'name': 'Harem', 'slug': 'harem'},
        {'name': 'Vida Escolar', 'slug': 'school-life'},
        {'name': 'Mecha', 'slug': 'mecha'},
        {'name': 'Reencarnación', 'slug': 'reincarnation'},
        {'name': 'Supervivencia', 'slug': 'survival'},
    ]
    for tag in tags:
        existing = db.query(Tag).filter_by(name=tag['name']).first()
        if not existing:
            db.add(Tag(**tag))

    # Filtros estáticos (webcomic, yonkoma, etc.)
    filter_options = [
        {'filter_type': 'webcomic', 'value': 'yes', 'description': 'Filtrar por webcomic'},
        {'filter_type': 'webcomic', 'value': 'no', 'description': 'No webcomic'},
        {'filter_type': 'yonkoma', 'value': 'yes', 'description': 'Filtrar por yonkoma'},
        {'filter_type': 'yonkoma', 'value': 'no', 'description': 'No yonkoma'},
        {'filter_type': 'amateur', 'value': 'yes', 'description': 'Filtrar por contenido amateur'},
        {'filter_type': 'amateur', 'value': 'no', 'description': 'No amateur'},
        {'filter_type': 'erotic', 'value': 'yes', 'description': 'Filtrar por contenido erótico'},
        {'filter_type': 'erotic', 'value': 'no', 'description': 'No erótico'},
    ]
    for fo in filter_options:
        existing = db.query(FilterOption).filter_by(filter_type=fo['filter_type'], value=fo['value']).first()
        if not existing:
            db.add(FilterOption(**fo))

    db.commit()

# Crear tablas y poblar datos estáticos
Base.metadata.create_all(bind=ENGINE)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Poblar datos estáticos al inicializar
if __name__ == "__main__":
    try:
        Base.metadata.create_all(bind=ENGINE)
        print("Tablas creadas exitosamente en la base de datos.")
        db = next(get_db())
        initialize_static_data(db)
        print("Datos estáticos inicializados.")
    except Exception as e:
        print(f"Error al crear las tablas o inicializar datos: {e}")

