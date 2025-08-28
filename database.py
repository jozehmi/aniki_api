# database.py - Configuración y definición de la base de datos en PostgreSQL con Supabase
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, DateTime, ForeignKey, Boolean, Float, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from enum import Enum as PythonEnum
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener la URL de la base de datos desde las variables de entorno
# El valor por defecto es solo un placeholder; la contraseña debe estar en .env
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.azawidatatlmzzpbhrrdjv:[YOUR-PASSWORD]@aws-1-us-east-2.pooler.supabase.com:5432/postgres")
ENGINE = create_engine(DATABASE_URL, echo=True)  # echo=True para logs de debug
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)

# Enum para Status
class MediaStatus(PythonEnum):
    EMISION = "emision"
    FINALIZADO = "finalizado"
    PROXIMAMENTE = "proximamente"

# Enum para Order
class MediaOrder(PythonEnum):
    PREDETERMINADO = "predeterminado"
    POPULAR = "popular"
    SCORE = "score"
    TITLE = "title"
    LATEST_ADDED = "latest_added"
    LATEST_RELEASED = "latest_released"

# Tablas
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)

class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(200), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    aka = Column(JSON, nullable=True)
    synopsis = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    next_date = Column(Date, nullable=True)
    wait_days = Column(Integer, nullable=True)
    status = Column(Enum(MediaStatus), nullable=True)
    runtime = Column(Integer, nullable=True)
    featured = Column(Boolean, default=False)
    mature = Column(Boolean, default=False)
    episodes_count = Column(Integer, nullable=True)
    score = Column(Float, nullable=True)
    votes = Column(Integer, nullable=True)
    mal_id = Column(Integer, nullable=True)
    seasons = Column(JSON, nullable=True)
    image_url = Column(String(500), nullable=True)
    backdrop = Column(String(500), nullable=True)
    trailer = Column(String(100), nullable=True)
    poster = Column(String(500), nullable=True)
    watch_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    type = Column(String(50), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    day = Column(String(50), nullable=True)
    time = Column(String(50), nullable=True)
    
    category = relationship("Category")
    genres = relationship("MediaGenre", back_populates="media")
    tags = relationship("MediaTag", back_populates="media")
    episodes = relationship("Episode", back_populates="media")

class MediaGenre(Base):
    __tablename__ = "media_genres"
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)
    genre_id = Column(Integer, ForeignKey("genres.id"), nullable=False)
    media = relationship("Media", back_populates="genres")

class MediaTag(Base):
    __tablename__ = "media_tags"
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)
    media = relationship("Media", back_populates="tags")

class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)
    number = Column(Integer, nullable=False)
    filler = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=True)
    image_url = Column(String(500), nullable=True)
    watch_url = Column(String(500), nullable=True)
    
    media = relationship("Media", back_populates="episodes")
    embeds = relationship("Embed", back_populates="episode")
    downloads = relationship("Download", back_populates="episode")

class Embed(Base):
    __tablename__ = "embeds"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False)
    server = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    variant = Column(String(50), nullable=True)
    
    episode = relationship("Episode", back_populates="embeds")

class Download(Base):
    __tablename__ = "downloads"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False)
    server = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    variant = Column(String(50), nullable=True)
    
    episode = relationship("Episode", back_populates="downloads")

class FilterOption(Base):
    __tablename__ = "filter_options"
    id = Column(Integer, primary_key=True, index=True)
    filter_type = Column(String(50), nullable=False)
    value = Column(String(100), nullable=False)
    is_multiple = Column(Boolean, default=False)

# Crear tablas al importar el módulo
Base.metadata.create_all(bind=ENGINE)

# Bloque para ejecución directa
if __name__ == "__main__":
    try:
        Base.metadata.create_all(bind=ENGINE)
        print("Tablas creadas exitosamente en la base de datos.")
    except Exception as e:
        print(f"Error al crear las tablas: {e}")