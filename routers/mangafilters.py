import os
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, ForeignKey, UniqueConstraint, Table
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
from enum import Enum as PyEnum

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///example.db")  # Fallback a SQLite si no hay DATABASE_URL
print(f"URL utilizada: {DATABASE_URL}")
ENGINE = create_engine(DATABASE_URL, echo=True)  # echo=True para logs de debug
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)

Base = declarative_base()

# Definir la tabla media_genres como una tabla simple (sin mapeador ORM)
media_genres = Table(
    "media_genres",
    Base.metadata,
    Column("media_id", Integer, ForeignKey("media.id"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True),
    Column("added_at", DateTime, nullable=False, default=datetime.utcnow)
)

class MediaStatus(PyEnum):
    PUBLISHING = "publishing"
    FINISHED = "finished"
    CANCELADO = "cancelado"
    PAUSADO = "paused"
    PROXIMAMENTE = "proximamente"
    EMISION = "emision"
    ACTIVE = "active"
    ABANDONED = "abandoned"

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    image_url = Column(String(255))
    source_url = Column(String(255))
    score = Column(Float)
    media_type_id = Column(Integer, ForeignKey("media_types.id"))
    demography_id = Column(Integer, ForeignKey("demography_types.id"))
    status = Column(Enum(MediaStatus))
    translation_status = Column(Enum(MediaStatus))
    mature = Column(Boolean, default=False)
    webcomic = Column(Boolean, default=False)
    yonkoma = Column(Boolean, default=False)
    amateur = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime)
    likes_count = Column(Integer, default=0)
    
    media_type = relationship("MediaType", back_populates="media")
    demography = relationship("DemographyType", back_populates="media")
    genres = relationship("Genre", secondary=media_genres, back_populates="medias")
    content_units = relationship("ContentUnit", back_populates="media")

class MediaType(Base):
    __tablename__ = "media_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    media = relationship("Media", back_populates="media_type")
    genres = relationship("Genre", back_populates="media_type")

class DemographyType(Base):
    __tablename__ = "demography_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    media = relationship("Media", back_populates="demography")

class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    media_type_id = Column(Integer, ForeignKey("media_types.id"), nullable=True)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    medias = relationship("Media", secondary=media_genres, back_populates="genres")
    media_type = relationship("MediaType", back_populates="genres")
    
    __table_args__ = (UniqueConstraint("slug", "media_type_id", name="uix_genre_slug_media_type"),)

class FilterOption(Base):
    __tablename__ = "filter_options"
    id = Column(Integer, primary_key=True, index=True)
    filter_type = Column(String(100), nullable=False)
    value = Column(String(100), nullable=False)
    description = Column(String(255))
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint("filter_type", "value", name="uix_filter_type_value"),)

class ContentUnit(Base):
    __tablename__ = "content_units"
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)
    type = Column(String(50), nullable=False)
    number = Column(Float, nullable=False)
    url = Column(String(255))
    title = Column(String(255))
    published_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    media = relationship("Media", back_populates="content_units")
    embeds = relationship("Embed", back_populates="content_unit")
    downloads = relationship("Download", back_populates="content_unit")

class Embed(Base):
    __tablename__ = "embeds"
    id = Column(Integer, primary_key=True, index=True)
    content_unit_id = Column(Integer, ForeignKey("content_units.id"), nullable=False)
    url = Column(String(255), nullable=False)
    source = Column(String(100))
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    content_unit = relationship("ContentUnit", back_populates="embeds")

class Download(Base):
    __tablename__ = "downloads"
    id = Column(Integer, primary_key=True, index=True)
    content_unit_id = Column(Integer, ForeignKey("content_units.id"), nullable=False)
    url = Column(String(255), nullable=False)
    source = Column(String(100))
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    content_unit = relationship("ContentUnit", back_populates="downloads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def initialize_static_data(db):
    # MediaTypes
    media_types = [
        {"name": "manga", "description": "Manga japonés"},
        {"name": "manhwa", "description": "Manga coreano"},
        {"name": "manhua", "description": "Manga chino"},
        {"name": "novel", "description": "Novela ligera"},
        {"name": "one_shot", "description": "Manga de un solo capítulo"},
        {"name": "doujinshi", "description": "Manga autopublicado"},
        {"name": "oel", "description": "Manga de estilo original en inglés"},
        {"name": "tv-anime", "description": "Anime de TV"},
        {"name": "pelicula", "description": "Película de anime"},
        {"name": "ova", "description": "Anime OVA"},
        {"name": "especial", "description": "Anime especial"}
    ]
    for mt in media_types:
        if not db.query(MediaType).filter(MediaType.name == mt["name"]).first():
            db.add(MediaType(name=mt["name"], description=mt["description"], added_at=datetime.utcnow()))
    db.commit()

    # DemographyTypes
    demography_types = [
        {"name": "seinen", "description": "Demografía para adultos jóvenes"},
        {"name": "shoujo", "description": "Demografía para chicas jóvenes"},
        {"name": "shounen", "description": "Demografía para chicos jóvenes"},
        {"name": "josei", "description": "Demografía para mujeres adultas"},
        {"name": "kodomo", "description": "Demografía para niños"}
    ]
    for dt in demography_types:
        if not db.query(DemographyType).filter(DemographyType.name == dt["name"]).first():
            db.add(DemographyType(name=dt["name"], description=dt["description"], added_at=datetime.utcnow()))
    db.commit()

    # Géneros para manga
    manga_genres = [
        {"name": "Acción", "slug": "action", "media_type_name": None},
        {"name": "Aventura", "slug": "adventure", "media_type_name": None},
        {"name": "Comedia", "slug": "comedy", "media_type_name": None},
        {"name": "Drama", "slug": "drama", "media_type_name": None},
        {"name": "Slice of Life", "slug": "slice-of-life", "media_type_name": None},
        {"name": "Ecchi", "slug": "ecchi", "media_type_name": None},
        {"name": "Fantasía", "slug": "fantasy", "media_type_name": None},
        {"name": "Magia", "slug": "magic", "media_type_name": None},
        {"name": "Sobrenatural", "slug": "supernatural", "media_type_name": None},
        {"name": "Horror", "slug": "horror", "media_type_name": None},
        {"name": "Misterio", "slug": "mystery", "media_type_name": None},
        {"name": "Psicológico", "slug": "psychological", "media_type_name": None},
        {"name": "Romance", "slug": "romance", "media_type_name": None},
        {"name": "Ciencia Ficción", "slug": "sci-fi", "media_type_name": None},
        {"name": "Thriller", "slug": "thriller", "media_type_name": None},
        {"name": "Deportes", "slug": "sports", "media_type_name": None},
        {"name": "Girls Love", "slug": "girls-love", "media_type_name": None},
        {"name": "Boys Love", "slug": "boys-love", "media_type_name": None},
        {"name": "Harem", "slug": "harem", "media_type_name": None},
        {"name": "Mecha", "slug": "mecha", "media_type_name": None},
        {"name": "Supervivencia", "slug": "survival", "media_type_name": "manga"},
        {"name": "Reencarnación", "slug": "reincarnation", "media_type_name": "manga"},
        {"name": "Gore", "slug": "gore", "media_type_name": None},
        {"name": "Apocalíptico", "slug": "apocalyptic", "media_type_name": None},
        {"name": "Tragedia", "slug": "tragedy", "media_type_name": None},
        {"name": "Vida Escolar", "slug": "school-life", "media_type_name": None},
        {"name": "Historia", "slug": "history", "media_type_name": None},
        {"name": "Militar", "slug": "military", "media_type_name": None},
        {"name": "Policía", "slug": "police", "media_type_name": None},
        {"name": "Crimen", "slug": "crime", "media_type_name": None},
        {"name": "Súper Poderes", "slug": "super-powers", "media_type_name": None},
        {"name": "Vampiros", "slug": "vampires", "media_type_name": None},
        {"name": "Artes Marciales", "slug": "martial-arts", "media_type_name": None},
        {"name": "Samurái", "slug": "samurai", "media_type_name": None},
        {"name": "Cambio de Género", "slug": "gender-bender", "media_type_name": None},
        {"name": "Realidad Virtual", "slug": "virtual-reality", "media_type_name": None},
        {"name": "Ciberpunk", "slug": "cyberpunk", "media_type_name": None},
        {"name": "Música", "slug": "music", "media_type_name": None},
        {"name": "Parodia", "slug": "parody", "media_type_name": None},
        {"name": "Animación", "slug": "animation", "media_type_name": None},
        {"name": "Demonios", "slug": "demons", "media_type_name": None},
        {"name": "Familia", "slug": "family", "media_type_name": None},
        {"name": "Extranjero", "slug": "foreign", "media_type_name": None},
        {"name": "Niños", "slug": "kids", "media_type_name": None},
        {"name": "Realidad", "slug": "reality", "media_type_name": None},
        {"name": "Telenovela", "slug": "soap-opera", "media_type_name": None},
        {"name": "Guerra", "slug": "war", "media_type_name": None},
        {"name": "Western", "slug": "western", "media_type_name": None},
        {"name": "Trampas", "slug": "traps", "media_type_name": None}
    ]
    # Géneros para anime
    anime_genres = [
        {"name": "Acción", "slug": "accion", "media_type_name": "tv-anime"},
        {"name": "Aventura", "slug": "aventura", "media_type_name": "tv-anime"},
        {"name": "Ciencia Ficción", "slug": "ciencia-ficcion", "media_type_name": "tv-anime"},
        {"name": "Comedia", "slug": "comedia", "media_type_name": "tv-anime"},
        {"name": "Deportes", "slug": "deportes", "media_type_name": "tv-anime"},
        {"name": "Drama", "slug": "drama", "media_type_name": "tv-anime"},
        {"name": "Fantasía", "slug": "fantasia", "media_type_name": "tv-anime"},
        {"name": "Misterio", "slug": "misterio", "media_type_name": "tv-anime"},
        {"name": "Recuentos de la Vida", "slug": "recuentos-de-la-vida", "media_type_name": "tv-anime"},
        {"name": "Romance", "slug": "romance", "media_type_name": "tv-anime"},
        {"name": "Seinen", "slug": "seinen", "media_type_name": "tv-anime"},
        {"name": "Shoujo", "slug": "shoujo", "media_type_name": "tv-anime"},
        {"name": "Shounen", "slug": "shounen", "media_type_name": "tv-anime"},
        {"name": "Sobrenatural", "slug": "sobrenatural", "media_type_name": "tv-anime"},
        {"name": "Suspenso", "slug": "suspenso", "media_type_name": "tv-anime"},
        {"name": "Terror", "slug": "terror", "media_type_name": "tv-anime"}
    ]
    for genre in manga_genres + anime_genres:
        media_type = db.query(MediaType).filter(MediaType.name == genre["media_type_name"]).first() if genre["media_type_name"] else None
        query = db.query(Genre).filter(Genre.slug == genre["slug"])
        if media_type:
            query = query.filter(Genre.media_type_id == media_type.id)
        else:
            query = query.filter(Genre.media_type_id.is_(None))
        if not query.first():
            db.add(Genre(
                name=genre["name"],
                slug=genre["slug"],
                media_type_id=media_type.id if media_type else None,
                added_at=datetime.utcnow()
            ))
    db.commit()

    # FilterOptions (manga y anime)
    manga_filters = {
        "order_item": ["likes_count", "title", "score", "created_at", "released_at", "chapters_count"],
        "order_dir": ["asc", "desc"],
        "type": ["manga", "manhwa", "manhua", "novel", "one_shot", "doujinshi", "oel"],
        "demography": ["seinen", "shoujo", "shounen", "josei", "kodomo"],
        "status": ["publishing", "finished", "canceled", "paused"],
        "translation_status": ["active", "finished", "abandoned"],
        "webcomic": ["yes", "no"],
        "yonkoma": ["yes", "no"],
        "amateur": ["yes", "no"],
        "erotic": ["yes", "no"],
        "genres": [
            "action", "adventure", "comedy", "drama", "slice-of-life", "ecchi", "fantasy", "magic",
            "supernatural", "horror", "mystery", "psychological", "romance", "sci-fi", "thriller",
            "sports", "girls-love", "boys-love", "harem", "mecha", "survival", "reincarnation",
            "gore", "apocalyptic", "tragedy", "school-life", "history", "military", "police",
            "crime", "super-powers", "vampires", "martial-arts", "samurai", "gender-bender",
            "virtual-reality", "cyberpunk", "music", "parody", "animation", "demons", "family",
            "foreign", "kids", "reality", "soap-opera", "war", "western", "traps"
        ],
        "exclude_genres": [
            "action", "adventure", "comedy", "drama", "slice-of-life", "ecchi", "fantasy", "magic",
            "supernatural", "horror", "mystery", "psychological", "romance", "sci-fi", "thriller",
            "sports", "girls-love", "boys-love", "harem", "mecha", "survival", "reincarnation",
            "gore", "apocalyptic", "tragedy", "school-life", "history", "military", "police",
            "crime", "super-powers", "vampires", "martial-arts", "samurai", "gender-bender",
            "virtual-reality", "cyberpunk", "music", "parody", "animation", "demons", "family",
            "foreign", "kids", "reality", "soap-opera", "war", "western", "traps"
        ]
    }
    anime_filters = {
        "Category": ["tv-anime", "pelicula", "ova", "especial"],
        "Genre": [
            "accion", "aventura", "ciencia-ficcion", "comedia", "deportes", "drama", "fantasia",
            "misterio", "recuentos-de-la-vida", "romance", "seinen", "shoujo", "shounen",
            "sobrenatural", "suspenso", "terror"
        ],
        "Status": ["emision", "finalizado", "proximamente"],
        "Order": ["predeterminado", "popular", "score", "title", "latest_added", "latest_released"],
        "Letter": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    }
    for filter_type, values in {**manga_filters, **anime_filters}.items():
        for value in values:
            if not db.query(FilterOption).filter(FilterOption.filter_type == filter_type, FilterOption.value == value).first():
                db.add(FilterOption(
                    filter_type=filter_type,
                    value=value,
                    description=f"Filtro {filter_type}: {value}",
                    added_at=datetime.utcnow()
                ))
    db.commit()

# Crear tablas automáticamente al importar el módulo
Base.metadata.create_all(ENGINE)

# Ejecutar initialize_static_data al importar el módulo
with SessionLocal() as db:
    initialize_static_data(db)

if __name__ == "__main__":
    print("Creando tablas y poblando datos iniciales...")
    Base.metadata.drop_all(ENGINE)  # Opcional: elimina tablas existentes para evitar conflictos
    Base.metadata.create_all(ENGINE)
    with SessionLocal() as db:
        initialize_static_data(db)
    print("Tablas creadas y datos iniciales poblados correctamente.")