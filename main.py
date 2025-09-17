from fastapi import FastAPI
from routers import animehome, animecatalog, animedetails, animeepisode, animeschedule, mangas, mangadetails, mangaimages, mangasearch
app = FastAPI(title="Anime & Manga API")

# Registrar routers
app.include_router(animehome.router, prefix="/api/animes", tags=["Animes Home"])
app.include_router(animecatalog.router, prefix="/api/animes", tags=["Animes Catalog"])
app.include_router(animedetails.router, prefix="/api/animes", tags=["Animes Details"])
app.include_router(animeepisode.router, prefix="/api/animes", tags=["Animes Episode"])
app.include_router(animeschedule.router, prefix="/api", tags=["Animes Schedule"])
app.include_router(mangas.router, prefix="/api/mangas", tags=["Mangas"])
app.include_router(mangadetails.router, prefix="/api/mangas", tags=["Manga Details"])
app.include_router(mangaimages.router, prefix="/api/mangas", tags=["Manga Images"])
app.include_router(mangasearch.router, prefix="/api/mangas", tags=["Manga Search"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
