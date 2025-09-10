from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, Date, DateTime,
    ForeignKey, Numeric, Table, Enum, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.dialects import postgresql
import enum
import os
from dotenv import load_dotenv # Importar load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está definida en las variables de entorno. "
                     "Asegúrate de tener un archivo .env con DATABASE_URL=postgresql://user:password@host:port/dbname")

print(f"URL de la base de datos utilizada: {DATABASE_URL}")

ENGINE = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)

# --- ENUMS ---
class MediaTypeEnum(enum.Enum):
    anime = "anime"
    manga = "manga"

class AnimeStatusEnum(enum.Enum):
    unknown = 0
    emision = 1
    finalizado = 2
    proximamente = 3

class MangaStatusEnum(enum.Enum):
    publishing = "publishing"
    finished = "finished"
    canceled = "canceled"
    paused = "paused"

class MangaTranslationStatusEnum(enum.Enum):
    active = "active"
    finished = "finished"
    abandoned = "abandoned"

class MangaOrderItemEnum(enum.Enum):
    likes_count = "likes_count"
    title = "title"
    score = "score"
    created_at = "created_at"
    released_at = "released_at"
    chapters_count = "chapters_count"

class OrderDirEnum(enum.Enum):
    asc = "asc"
    desc = "desc"

class YesNoEnum(enum.Enum):
    yes = "yes"
    no = "no"

# --- TABLAS PRINCIPALES ---

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    media_type = Column(Enum(MediaTypeEnum), nullable=False) # 'anime' o 'manga'

    animes = relationship("Anime", back_populates="category")
    mangas = relationship("Manga", back_populates="category")

class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    applies_to = Column(postgresql.ARRAY(String), nullable=False)  # ["anime"], ["manga"], ["anime","manga"]


# Tabla Anime
class Anime(Base):
    __tablename__ = "anime"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    aka_ja_jp = Column(postgresql.JSONB)
    synopsis = Column(Text)
    poster_url = Column(String(255)) # cover en search, poster en slug
    backdrop_url = Column(String(255)) # image_url en featured
    trailer_id = Column(String(50))
    watch_url = Column(String(255)) # URL para ver el anime
    status = Column(Enum(AnimeStatusEnum))
    runtime = Column(Integer)
    start_date = Column(Date)
    next_date = Column(DateTime(timezone=True))
    end_date = Column(Date)
    wait_days = Column(Integer)
    featured = Column(Boolean, default=False)
    mature = Column(Boolean, default=False)
    episodes_count = Column(Integer)
    score = Column(Numeric(3, 2))
    votes = Column(Integer)
    slug = Column(String(255), unique=True, nullable=False)
    mal_id = Column(Integer)
    seasons = Column(Integer) # Añadido: seasons
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    category_id = Column(Integer, ForeignKey("categories.id"))

    category = relationship("Category", back_populates="animes")
    genres = relationship("Genre", secondary="anime_genres", back_populates="animes")
    episodes = relationship("Episode", back_populates="anime")
    relations_as_source = relationship("MediaRelation", foreign_keys="MediaRelation.source_media_id", primaryjoin="and_(MediaRelation.source_media_id==Anime.id, MediaRelation.source_media_type=='anime')")
    relations_as_destination = relationship("MediaRelation", foreign_keys="MediaRelation.destination_media_id", primaryjoin="and_(MediaRelation.destination_media_id==Anime.id, MediaRelation.destination_media_type=='anime')")
    schedule_entries = relationship("AnimeSchedule", back_populates="anime")

# Tabla Manga
class Manga(Base):
    __tablename__ = "manga"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255))
    description = Column(Text)
    cover_url = Column(String(255)) # cover en home, cover en detalle
    type = Column(String(50)) # 'manga', 'manhua', 'manhwa', etc.
    demography = Column(String(50)) # 'Shounen', 'Seinen', 'Josei', etc.
    state = Column(String(50)) # 'Publicándose', 'Finalizado', etc.
    status = Column(Enum(MangaStatusEnum))
    translation_status = Column(Enum(MangaTranslationStatusEnum))
    webcomic = Column(Enum(YesNoEnum))
    yonkoma = Column(Enum(YesNoEnum))
    amateur = Column(Enum(YesNoEnum))
    erotic = Column(Enum(YesNoEnum))
    score = Column(Numeric(3, 2))
    popularity = Column(Integer)
    url = Column(String(255), unique=True) # URL de la fuente original (zonatmo.com/library/manga/...)
    alt_titles = Column(postgresql.ARRAY(String))
    synonyms = Column(postgresql.ARRAY(String))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    category_id = Column(Integer, ForeignKey("categories.id")) # Aunque el JSON no lo usa, es buena práctica

    category = relationship("Category", back_populates="mangas")
    chapters = relationship("Chapter", back_populates="manga")
    genres = relationship("Genre", secondary="manga_genres", back_populates="mangas")
    relations_as_source = relationship("MediaRelation", foreign_keys="MediaRelation.source_media_id", primaryjoin="and_(MediaRelation.source_media_id==Manga.id, MediaRelation.source_media_type=='manga')")
    relations_as_destination = relationship("MediaRelation", foreign_keys="MediaRelation.destination_media_id", primaryjoin="and_(MediaRelation.destination_media_id==Manga.id, MediaRelation.destination_media_type=='manga')")


# --- TABLAS DE UNIÓN (MANY-TO-MANY) ---

anime_genres = Table(
    "anime_genres", Base.metadata,
    Column("anime_id", Integer, ForeignKey("anime.id"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True)
)

manga_genres = Table(
    "manga_genres", Base.metadata,
    Column("manga_id", Integer, ForeignKey("manga.id"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True)
)

# Añadimos back_populates para géneros
Genre.animes = relationship("Anime", secondary=anime_genres, back_populates="genres")
Genre.mangas = relationship("Manga", secondary=manga_genres, back_populates="genres")


# --- TABLAS DE CONTENIDO ESPECÍFICO ---

class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True)
    anime_id = Column(Integer, ForeignKey("anime.id"), nullable=False)
    number = Column(Integer, nullable=False)
    filler = Column(Boolean, default=False)
    image_url = Column(String(255)) # image en slug, thumbnail en latestEpisodes
    watch_url = Column(String(255))
    created_at = Column(DateTime(timezone=True))
    published_at = Column(DateTime(timezone=True)) # latestEpisodes usa publishedAt

    anime = relationship("Anime", back_populates="episodes")
    embeds = relationship("Embed", back_populates="episode")
    downloads = relationship("Download", back_populates="episode")

    __table_args__ = (UniqueConstraint("anime_id", "number", name="uq_anime_episode_number"),)


class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True)
    manga_id = Column(Integer, ForeignKey("manga.id"), nullable=False)
    number = Column(Numeric(6, 2), nullable=False) # Permite 2.50, 3.00
    title = Column(String(255))
    url = Column(String(255)) # URL de la subida del capítulo (view_uploads)
    date = Column(Date) # Fecha de subida del capítulo
    group = Column(String(100)) # Grupo que lo subió
    created_at = Column(DateTime(timezone=True)) # Para tracking interno

    manga = relationship("Manga", back_populates="chapters")
    embeds = relationship("Embed", back_populates="chapter")
    downloads = relationship("Download", back_populates="chapter")

    __table_args__ = (UniqueConstraint("manga_id", "number", name="uq_manga_chapter_number"),)


# --- TABLAS DE ENLACES (EMBEDS/DOWNLOADS) ---

class Embed(Base):
    __tablename__ = "embeds"
    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    server = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    variant = Column(String(50)) # Ej: 'SUB', 'DUB'

    episode = relationship("Episode", back_populates="embeds")
    chapter = relationship("Chapter", back_populates="embeds")


class Download(Base):
    __tablename__ = "downloads"
    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    server = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    variant = Column(String(50)) # Ej: 'SUB', 'DUB'

    episode = relationship("Episode", back_populates="downloads")
    chapter = relationship("Chapter", back_populates="downloads")


# --- TABLAS DE RELACIONES ENTRE MEDIOS ---

class RelationType(Base): # Añadido: Tabla para tipos de relación
    __tablename__ = "relation_types"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False) # Ej: 'Película', 'Precuela', 'Secuela', 'Arco'
    api_code = Column(Integer, unique=True, nullable=False) # Ej: 10 para película, 4 para arco

class MediaRelation(Base):
    __tablename__ = "media_relations"
    id = Column(Integer, primary_key=True)
    source_media_type = Column(Enum(MediaTypeEnum), nullable=False)
    source_media_id = Column(Integer, nullable=False)
    relation_type_id = Column(Integer, ForeignKey("relation_types.id")) # FK a RelationType
    destination_media_type = Column(Enum(MediaTypeEnum), nullable=False)
    destination_media_id = Column(Integer, nullable=False)

    relation_type = relationship("RelationType")

    __table_args__ = (
        UniqueConstraint(
            "source_media_type", "source_media_id", "relation_type_id",
            "destination_media_type", "destination_media_id",
            name="uq_media_relation"
        ),
    )

# --- TABLA PARA HORARIO DE ANIME ---
class AnimeSchedule(Base): # Añadido: Tabla para horario de anime
    __tablename__ = "anime_schedule"
    id = Column(Integer, primary_key=True)
    anime_id = Column(Integer, ForeignKey("anime.id"), nullable=False)
    day = Column(String(20), nullable=False) # Ej: 'Domingo', 'Miércoles'
    time = Column(String(20), nullable=False) # Ej: '10:05 pm', '08:48 pm'
    latest_episode_id = Column(Integer, ForeignKey("episodes.id")) # Último episodio emitido en este horario
    
    anime = relationship("Anime", back_populates="schedule_entries")
    latest_episode = relationship("Episode")


# --- TABLAS PARA SECCIONES HOME (ANIME) ---

class AnimeHomeSection(Base):
    __tablename__ = "anime_home_sections"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False) # 'featured', 'latestEpisodes', 'latestMedia'

class AnimeHomeFeatured(Base):
    __tablename__ = "anime_home_featured"
    id = Column(Integer, primary_key=True)
    anime_id = Column(Integer, ForeignKey("anime.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("anime_home_sections.id"), nullable=False)
    position = Column(Integer) # Para ordenar si es necesario
    created_at = Column(DateTime(timezone=True)) # No default aquí, se espera que la API lo proporcione
    
    anime = relationship("Anime")
    section = relationship("AnimeHomeSection")

class AnimeHomeLatestEpisode(Base):
    __tablename__ = "anime_home_latest_episodes"
    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("anime_home_sections.id"), nullable=False)
    created_at = Column(DateTime(timezone=True)) # No default aquí
    
    episode = relationship("Episode")
    section = relationship("AnimeHomeSection")

class AnimeHomeLatestMedia(Base):
    __tablename__ = "anime_home_latest_media"
    id = Column(Integer, primary_key=True)
    media_type = Column(Enum(MediaTypeEnum), nullable=False) # Siempre 'anime' en este caso, pero útil para consistencia
    media_id = Column(Integer, nullable=False) # ID del anime
    section_id = Column(Integer, ForeignKey("anime_home_sections.id"), nullable=False)
    created_at = Column(DateTime(timezone=True)) # No default aquí

    section = relationship("AnimeHomeSection")


# --- TABLAS PARA SECCIONES HOME (MANGA) ---

class MangaHomeSection(Base):
    __tablename__ = "manga_home_sections"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False) # 'populares_general', 'trending_seinen', 'ultimos_anadidos', etc.

class MangaHomeItem(Base):
    __tablename__ = "manga_home_items"
    id = Column(Integer, primary_key=True)
    manga_id = Column(Integer, ForeignKey("manga.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("manga_home_sections.id"), nullable=False)
    position = Column(Integer) # Para ordenar si es necesario
    chapter_number = Column(Numeric(6,2)) # Añadido: chapter_number para ultimas_subidas
    upload_time = Column(String(20)) # Añadido: upload_time para ultimas_subidas
    created_at = Column(DateTime(timezone=True)) # Para tracking interno de cuándo se añadió a esta sección
    
    manga = relationship("Manga")
    section = relationship("MangaHomeSection")


# --- TABLAS PARA FILTROS ESTÁTICOS ---

class AnimeFilterOption(Base):
    __tablename__ = "anime_filter_options"
    id = Column(Integer, primary_key=True)
    filter_name = Column(String(50), nullable=False) # Ej: 'Category', 'Genre', 'Status', 'Order', 'Letter'
    option_value = Column(String(100), nullable=False)
    option_label = Column(String(100)) # Si es diferente al valor
    option_type = Column(String(20)) # 'multiple', 'single', 'integer'
    min_value = Column(Integer) # Para filtros de rango (minYear)
    max_value = Column(Integer) # Para filtros de rango (maxYear)

    __table_args__ = (UniqueConstraint("filter_name", "option_value", name="uq_anime_filter_option"),)

class MangaFilterOption(Base):
    __tablename__ = "manga_filter_options"
    id = Column(Integer, primary_key=True)
    filter_name = Column(String(50), nullable=False) # Ej: 'type', 'demography', 'status', 'genres'
    option_value = Column(String(100), nullable=False)
    option_label = Column(String(100)) # Si es diferente al valor
    option_type = Column(String(20)) # 'string', 'list', 'integer'
    default_value = Column(String(100)) # Para order_item, order_dir, page
    min_value = Column(Integer) # Para page
    max_value = Column(Integer) # Para page

    __table_args__ = (UniqueConstraint("filter_name", "option_value", name="uq_manga_filter_option"),)


# --- FUNCIONES DE UTILIDAD ---

def create_all_tables():
    """
    Crea todas las tablas definidas en la base de datos PostgreSQL.
    """
    Base.metadata.create_all(ENGINE)
    print("Base de datos y tablas creadas con éxito.")

def get_db():
    """
    Generador para obtener una sesión de base de datos.
    Debe usarse con 'with' o en un bloque try-finally para asegurar el cierre.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    # Asegúrate de que el archivo .env existe y contiene DATABASE_URL
    # Ejemplo de .env:
    # DATABASE_URL="postgresql://user:password@localhost:5432/anime_manga_db"

    create_all_tables()

    # --- INSERCIÓN DE DATOS INICIALES (CATEGORÍAS, GÉNEROS, SECCIONES HOME, FILTROS) ---
    # Usamos get_db() para obtener una sesión
    with next(get_db()) as session:
        try:
            # Categorías de Anime
            anime_categories = [
                Category(id=1, name="TV Anime", slug="tv-anime", media_type=MediaTypeEnum.anime),
                Category(id=2, name="Película", slug="pelicula", media_type=MediaTypeEnum.anime),
                Category(id=3, name="OVA", slug="ova", media_type=MediaTypeEnum.anime),
                Category(id=4, name="Especial", slug="especial", media_type=MediaTypeEnum.anime),
            ]
            session.add_all(anime_categories)

            # Categorías de Manga (usando 'type' y 'demography' del JSON de filtros de manga)
            manga_types = [
                Category(id=5, name="Manga", slug="manga", media_type=MediaTypeEnum.manga),
                Category(id=6, name="Manhua", slug="manhua", media_type=MediaTypeEnum.manga),
                Category(id=7, name="Manhwa", slug="manhwa", media_type=MediaTypeEnum.manga),
                Category(id=8, name="Novel", slug="novel", media_type=MediaTypeEnum.manga),
                Category(id=9, name="One Shot", slug="one_shot", media_type=MediaTypeEnum.manga),
                Category(id=10, name="Doujinshi", slug="doujinshi", media_type=MediaTypeEnum.manga),
                Category(id=11, name="OEL", slug="oel", media_type=MediaTypeEnum.manga),
            ]
            session.add_all(manga_types)

            # Géneros (ejemplo, deberías insertar todos los de tus filtros)
            genres_data = [
                    # Ambos
                    Genre(name="Acción", slug="accion", applies_to=["anime", "manga"]),
                    Genre(name="Aventura", slug="aventura", applies_to=["anime", "manga"]),
                    Genre(name="Comedia", slug="comedia", applies_to=["anime", "manga"]),
                    Genre(name="Drama", slug="drama", applies_to=["anime", "manga"]),
                    Genre(name="Fantasía", slug="fantasia", applies_to=["anime", "manga"]),
                    Genre(name="Misterio", slug="misterio", applies_to=["anime", "manga"]),
                    Genre(name="Romance", slug="romance", applies_to=["anime", "manga"]),
                    Genre(name="Sobrenatural", slug="sobrenatural", applies_to=["anime", "manga"]),
                    Genre(name="Suspenso", slug="suspenso", applies_to=["anime", "manga"]),
                    Genre(name="Terror", slug="terror", applies_to=["anime", "manga"]),
                    Genre(name="Deportes", slug="deportes", applies_to=["anime", "manga"]),

                    # Solo Manga
                    Genre(name="Slice of Life", slug="slice_of_life", applies_to=["manga"]),
                    Genre(name="Ecchi", slug="ecchi", applies_to=["manga"]),
                    Genre(name="Magic", slug="magic", applies_to=["manga"]),
                    Genre(name="Supernatural", slug="supernatural", applies_to=["manga"]),
                    Genre(name="Psychological", slug="psychological", applies_to=["manga"]),
                    Genre(name="Sci-Fi", slug="sci_fi", applies_to=["manga"]),
                    Genre(name="Thriller", slug="thriller", applies_to=["manga"]),
                    Genre(name="Girls Love", slug="girls_love", applies_to=["manga"]),
                    Genre(name="Boys Love", slug="boys_love", applies_to=["manga"]),
                    Genre(name="Harem", slug="harem", applies_to=["manga"]),
                    Genre(name="Mecha", slug="mecha", applies_to=["manga"]),
                    Genre(name="Survival", slug="survival", applies_to=["manga"]),
                    Genre(name="Reincarnation", slug="reincarnation", applies_to=["manga"]),
                    Genre(name="Gore", slug="gore", applies_to=["manga"]),
                    Genre(name="Apocalyptic", slug="apocalyptic", applies_to=["manga"]),
                    Genre(name="Tragedy", slug="tragedy", applies_to=["manga"]),
                    Genre(name="School Life", slug="school_life", applies_to=["manga"]),
                    Genre(name="History", slug="history", applies_to=["manga"]),
                    Genre(name="Military", slug="military", applies_to=["manga"]),
                    Genre(name="Police", slug="police", applies_to=["manga"]),
                    Genre(name="Crime", slug="crime", applies_to=["manga"]),
                    Genre(name="Super Powers", slug="super_powers", applies_to=["manga"]),
                    Genre(name="Vampires", slug="vampires", applies_to=["manga"]),
                    Genre(name="Martial Arts", slug="martial_arts", applies_to=["manga"]),
                    Genre(name="Samurai", slug="samurai", applies_to=["manga"]),
                    Genre(name="Gender Bender", slug="gender_bender", applies_to=["manga"]),
                    Genre(name="Virtual Reality", slug="virtual_reality", applies_to=["manga"]),
                    Genre(name="Cyberpunk", slug="cyberpunk", applies_to=["manga"]),
                    Genre(name="Music", slug="music", applies_to=["manga"]),
                    Genre(name="Parody", slug="parody", applies_to=["manga"]),
                    Genre(name="Animation", slug="animation", applies_to=["manga"]),
                    Genre(name="Demons", slug="demons", applies_to=["manga"]),
                    Genre(name="Family", slug="family", applies_to=["manga"]),
                    Genre(name="Foreign", slug="foreign", applies_to=["manga"]),
                    Genre(name="Kids", slug="kids", applies_to=["manga"]),
                    Genre(name="Reality", slug="reality", applies_to=["manga"]),
                    Genre(name="Soap Opera", slug="soap_opera", applies_to=["manga"]),
                    Genre(name="War", slug="war", applies_to=["manga"]),
                    Genre(name="Western", slug="western", applies_to=["manga"]),
                    Genre(name="Traps", slug="traps", applies_to=["manga"]),

                    # Solo Anime
                    Genre(name="Ciencia Ficción", slug="ciencia-ficcion", applies_to=["anime"]),
                    Genre(name="Recuentos de la vida", slug="recuentos-de-la-vida", applies_to=["anime"]),
                    Genre(name="Seinen", slug="seinen", applies_to=["anime"]),
                    Genre(name="Shoujo", slug="shoujo", applies_to=["anime"]),
                    Genre(name="Shounen", slug="shounen", applies_to=["anime"]),
                ]
            session.add_all(genres_data)

            # Tipos de Relación
            relation_types_data = [
                RelationType(id=1, name="Secuela", api_code=1),
                RelationType(id=2, name="Precuela", api_code=2),
                RelationType(id=3, name="Historia Alternativa", api_code=3),
                RelationType(id=4, name="Arco", api_code=4), # One Piece: Gyojin Tou-hen
                RelationType(id=5, name="Spin-off", api_code=5),
                RelationType(id=6, name="Adaptación", api_code=6),
                RelationType(id=7, name="Otro", api_code=7),
                RelationType(id=8, name="Resumen", api_code=8),
                RelationType(id=9, name="Side Story", api_code=9),
                RelationType(id=10, name="Película", api_code=10), # One Piece Film: Z, Red
            ]
            session.add_all(relation_types_data)

            # Secciones Home de Anime
            anime_home_sections = [
                AnimeHomeSection(id=1, name="featured"),
                AnimeHomeSection(id=2, name="latestEpisodes"),
                AnimeHomeSection(id=3, name="latestMedia"),
            ]
            session.add_all(anime_home_sections)

            # Secciones Home de Manga
            manga_home_sections = [
                MangaHomeSection(id=1, name="populares_general"),
                MangaHomeSection(id=2, name="populares_seinen"),
                MangaHomeSection(id=3, name="populares_josei"),
                MangaHomeSection(id=4, name="trending_general"),
                MangaHomeSection(id=5, name="trending_seinen"),
                MangaHomeSection(id=6, name="trending_josei"),
                MangaHomeSection(id=7, name="ultimos_anadidos"),
                MangaHomeSection(id=8, name="ultimas_subidas"),
                MangaHomeSection(id=9, name="top_semanal"),
                MangaHomeSection(id=10, name="top_mensual"),
            ]
            session.add_all(manga_home_sections)

            # Filtros de Anime (ejemplo, deberías insertar todos los de tu JSON)
            anime_filters = [
                AnimeFilterOption(filter_name="Category", option_value="tv-anime", option_type="multiple"),
                AnimeFilterOption(filter_name="Category", option_value="pelicula", option_type="multiple"),
                AnimeFilterOption(filter_name="Category", option_value="ova", option_type="multiple"),
                AnimeFilterOption(filter_name="Category", option_value="especial", option_type="multiple"),
                AnimeFilterOption(filter_name="Genre", option_value="accion", option_type="multiple"),
                AnimeFilterOption(filter_name="minYear", option_value="1990", option_type="integer", min_value=1990, max_value=2025),
                AnimeFilterOption(filter_name="maxYear", option_value="2025", option_type="integer", min_value=1990, max_value=2025),
                AnimeFilterOption(filter_name="Status", option_value="emision", option_type="single"),
                AnimeFilterOption(filter_name="Status", option_value="finalizado", option_type="single"),
                AnimeFilterOption(filter_name="Status", option_value="proximamente", option_type="single"),
                AnimeFilterOption(filter_name="Order", option_value="predeterminado", option_type="single"),
                AnimeFilterOption(filter_name="Order", option_value="popular", option_type="single"),
                AnimeFilterOption(filter_name="Order", option_value="score", option_type="single"),
                AnimeFilterOption(filter_name="Order", option_value="title", option_type="single"),
                AnimeFilterOption(filter_name="Order", option_value="latest_added", option_type="single"),
                AnimeFilterOption(filter_name="Order", option_value="latest_released", option_type="single"),
                AnimeFilterOption(filter_name="Letter", option_value="A", option_type="single"), # ... hasta Z
                AnimeFilterOption(filter_name="Page", option_value="1", option_type="integer", min_value=1),
            ]
            session.add_all(anime_filters)

            # Filtros de Manga (ejemplo, deberías insertar todos los de tu JSON)
            manga_filters = [
                MangaFilterOption(filter_name="title", option_value="", option_type="string", default_value=""),
                MangaFilterOption(filter_name="order_item", option_value="likes_count", option_type="string", default_value="likes_count"),
                MangaFilterOption(filter_name="order_item", option_value="title", option_type="string"),
                MangaFilterOption(filter_name="order_item", option_value="score", option_type="string"),
                MangaFilterOption(filter_name="order_item", option_value="created_at", option_type="string"),
                MangaFilterOption(filter_name="order_item", option_value="released_at", option_type="string"),
                MangaFilterOption(filter_name="order_item", option_value="chapters_count", option_type="string"),
                MangaFilterOption(filter_name="order_dir", option_value="desc", option_type="string", default_value="desc"),
                MangaFilterOption(filter_name="order_dir", option_value="asc", option_type="string"),
                MangaFilterOption(filter_name="type", option_value="manga", option_type="string"), # ... todos los tipos
                MangaFilterOption(filter_name="demography", option_value="seinen", option_type="string"), # ... todas las demografías
                MangaFilterOption(filter_name="status", option_value="publishing", option_type="string"), # ... todos los estados
                MangaFilterOption(filter_name="translation_status", option_value="active", option_type="string"), # ... todos los estados
                MangaFilterOption(filter_name="webcomic", option_value="yes", option_type="string"),
                MangaFilterOption(filter_name="yonkoma", option_value="yes", option_type="string"),
                MangaFilterOption(filter_name="amateur", option_value="yes", option_type="string"),
                MangaFilterOption(filter_name="erotic", option_value="yes", option_type="string"),
                MangaFilterOption(filter_name="genres", option_value="action", option_type="list"), # ... todos los géneros
                MangaFilterOption(filter_name="exclude_genres", option_value="action", option_type="list"), # ... todos los géneros
                MangaFilterOption(filter_name="page", option_value="1", option_type="integer", default_value="1", min_value=1),
            ]
            session.add_all(manga_filters)

            session.commit()
            print("Datos iniciales insertados con éxito.")

        except Exception as e:
            session.rollback()
            print(f"Error al insertar datos iniciales: {e}")
        finally:
            session.close()

