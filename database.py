from sqlalchemy import create_engine, Column, Integer, String, Date, Text, DateTime, ForeignKey, Boolean, Float, JSON, Enum, UniqueConstraint
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
from enum import Enum as PythonEnum
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está definida en las variables de entorno")
print(f"URL utilizada: {DATABASE_URL}")
ENGINE = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)

# --------------------------
# Enums
# --------------------------
class MediaStatus(PythonEnum):
    EMISION = "emision"
    FINALIZADO = "finalizado"
    PROXIMAMENTE = "proximamente"
    CANCELADO = "canceled"
    PAUSADO = "paused"
    PUBLISHING = "publishing"
    FINISHED = "finished"
    ABANDONED = "abandoned"

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

# --------------------------
# Tablas principales
# --------------------------
class MediaType(Base):
    __tablename__ = "media_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # ej: tv-anime, manga
    description = Column(Text, nullable=True)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    genres = relationship("Genre", back_populates="media_type")

class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    media_type_id = Column(Integer, ForeignKey("media_types.id"), nullable=False)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    media_type = relationship("MediaType", back_populates="genres")
    __table_args__ = (UniqueConstraint("slug", "media_type_id", name="uix_genre_slug_media_type"),)

# --------------------------
# Filtros dinámicos
# --------------------------
class FilterCategory(Base):
    __tablename__ = "filter_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)  # ej: Genre, Status, Boolean
    type = Column(String(20), nullable=False)  # single, multiple, integer, string
    options = relationship("FilterOption", back_populates="category")

class FilterOption(Base):
    __tablename__ = "filter_options"
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("filter_categories.id"), nullable=False)
    value = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = relationship("FilterCategory", back_populates="options")
    media_relations = relationship("FilterMediaTypeRelation", back_populates="filter_option")
    __table_args__ = (UniqueConstraint("category_id", "value", name="uix_category_value"),)

class FilterMediaTypeRelation(Base):
    __tablename__ = "filter_media_type_relation"
    id = Column(Integer, primary_key=True, index=True)
    filter_option_id = Column(Integer, ForeignKey("filter_options.id"), nullable=False)
    media_type_id = Column(Integer, ForeignKey("media_types.id"), nullable=False)
    filter_option = relationship("FilterOption", back_populates="media_relations")
    media_type = relationship("MediaType")

# --------------------------
# Media principal
# --------------------------
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
    translation_status = Column(Enum(MediaStatus), nullable=True)
    score = Column(Float, nullable=True)
    votes = Column(Integer, nullable=True)
    likes_count = Column(Integer, nullable=True)
    image_url = Column(String(500), nullable=True)
    backdrop_url = Column(String(500), nullable=True)
    trailer_url = Column(String(500), nullable=True)
    watch_url = Column(String(500), nullable=True)
    source_url = Column(String(500), nullable=True)
    mature = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    webcomic = Column(Boolean, default=False)
    yonkoma = Column(Boolean, default=False)
    amateur = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    media_type_id = Column(Integer, ForeignKey("media_types.id"), nullable=False)
    media_type = relationship("MediaType")
    genres = relationship("MediaGenre", back_populates="media")

class MediaGenre(Base):
    __tablename__ = "media_genres"
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)
    genre_id = Column(Integer, ForeignKey("genres.id"), nullable=False)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    media = relationship("Media", back_populates="genres")
    genre = relationship("Genre")

# --------------------------
# Función de inicialización
# --------------------------
def initialize_static_data(db):
    # --------------------------
    # Media Types
    # --------------------------
    media_types = [
        {'name': 'tv-anime', 'description': 'Series de anime transmitidas en TV'},
        {'name': 'pelicula', 'description': 'Películas de anime'},
        {'name': 'ova', 'description': 'Original Video Animation'},
        {'name': 'especial', 'description': 'Episodios especiales de anime'},
        {'name': 'manga', 'description': 'Cómics japoneses'},
        {'name': 'manhwa', 'description': 'Cómics coreanos'},
        {'name': 'manhua', 'description': 'Cómics chinos'},
        {'name': 'novel', 'description': 'Novelas ligeras'},
        {'name': 'one_shot', 'description': 'Historias de un solo capítulo'},
        {'name': 'doujinshi', 'description': 'Obras autoeditadas, usualmente fan-made'},
        {'name': 'oel', 'description': 'Original English Language manga'},
    ]
    for mt in media_types:
        if not db.query(MediaType).filter_by(name=mt['name']).first():
            db.add(MediaType(**mt))
    db.commit()
    
    # --------------------------
    # Géneros
    # --------------------------
    genres = [
        {"name": "Acción", "slug": "accion"},
        {"name": "Aventura", "slug": "aventura"},
        {"name": "Comedia", "slug": "comedia"},
        {"name": "Drama", "slug": "drama"},
        {"name": "Fantasía", "slug": "fantasia"},
        {"name": "Misterio", "slug": "misterio"},
        {"name": "Romance", "slug": "romance"},
        {"name": "Sobrenatural", "slug": "sobrenatural"},
        {"name": "Shounen", "slug": "shounen"},
        {"name": "Seinen", "slug": "seinen"},
        {"name": "Shoujo", "slug": "shoujo"},
        {"name": "Ciencia Ficción", "slug": "ciencia-ficcion"},
        {"name": "Deportes", "slug": "deportes"},
        {"name": "Recuentos de la Vida", "slug": "recuentos-de-la-vida"},
        {"name": "Suspenso", "slug": "suspenso"},
        {"name": "Terror", "slug": "terror"},
        {"name": "Ecchi", "slug": "ecchi"},
        {"name": "Psicológico", "slug": "psychological"},
        {"name": "Girls Love", "slug": "girls_love"},
        {"name": "Boys Love", "slug": "boys_love"},
        {"name": "Supervivencia", "slug": "survival"},
        {"name": "Reencarnación", "slug": "reincarnation"},
        {"name": "Gore", "slug": "gore"},
        {"name": "Apocalíptico", "slug": "apocalyptic"},
        {"name": "Tragedia", "slug": "tragedy"},
        {"name": "Vida Escolar", "slug": "school_life"},
        {"name": "Historia", "slug": "history"},
        {"name": "Militar", "slug": "military"},
        {"name": "Policía", "slug": "police"},
        {"name": "Crimen", "slug": "crime"},
        {"name": "Superpoderes", "slug": "super_powers"},
        {"name": "Vampiros", "slug": "vampires"},
        {"name": "Artes Marciales", "slug": "martial_arts"},
        {"name": "Samurái", "slug": "samurai"},
        {"name": "Género Bender", "slug": "gender_bender"},
        {"name": "Realidad Virtual", "slug": "virtual_reality"},
        {"name": "Cyberpunk", "slug": "cyberpunk"},
        {"name": "Música", "slug": "music"},
        {"name": "Parodia", "slug": "parody"},
        {"name": "Animación", "slug": "animation"},
        {"name": "Demonios", "slug": "demons"},
        {"name": "Familia", "slug": "family"},
        {"name": "Extranjero", "slug": "foreign"},
        {"name": "Niños", "slug": "kids"},
        {"name": "Realidad", "slug": "reality"},
        {"name": "Telenovela", "slug": "soap_opera"},
        {"name": "Guerra", "slug": "war"},
        {"name": "Western", "slug": "western"},
        {"name": "Trampas", "slug": "traps"},
    ]
    media_types = db.query(MediaType).all()
    for genre in genres:
        for mt in media_types:
            if not db.query(Genre).filter_by(slug=genre["slug"], media_type_id=mt.id).first():
                db.add(Genre(
                    name=genre["name"],
                    slug=genre["slug"],
                    media_type_id=mt.id,
                    added_at=datetime.utcnow()
                ))
    db.commit()

    # --------------------------
    # Filtros
    # --------------------------
    filters = {
        "Boolean": ["webcomic", "yonkoma", "amateur", "erotic"],
        "Status": ["publishing", "finished", "canceled", "paused"],
        "Translation Status": ["active", "finished", "abandoned"],
        "Order": ["likes_count", "title", "score", "created_at", "released_at", "chapters_count"]
    }

    for cat_name, options in filters.items():
        # Crear categoría si no existe
        category = db.query(FilterCategory).filter_by(name=cat_name).first()
        if not category:
            category = FilterCategory(name=cat_name, type="single" if cat_name != "Boolean" else "multiple")
            db.add(category)
            db.commit()
        # Agregar opciones
        for opt in options:
            if not db.query(FilterOption).filter_by(category_id=category.id, value=opt).first():
                db.add(FilterOption(category_id=category.id, value=opt, description=f"Filtro {opt}"))
        db.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------
# Crear tablas e inicializar
# --------------------------
if __name__ == "__main__":
    try:
        Base.metadata.create_all(bind=ENGINE)
        print("Tablas creadas exitosamente en la base de datos.")
        db = next(get_db())
        initialize_static_data(db)
        print("Datos estáticos inicializados.")
    except Exception as e:
        print(f"Error al crear las tablas o inicializar datos: {e}")
