from fastapi import APIRouter, Depends
from datetime import datetime
from core.config import VALID_CATEGORIES, VALID_GENRES, VALID_STATUS, VALID_ORDERS, VALID_LETTERS
from sqlalchemy.orm import Session
from database import get_db
from save_anime_functions import save_filters

router = APIRouter()

@router.get("/filters")
def get_filters(db: Session = Depends(get_db)):
    current_year = datetime.now().year
    
    # Definir los filtros
    filters_data = {
        "Category": {"type": "multiple", "options": VALID_CATEGORIES},
        "Genre": {"type": "multiple", "options": VALID_GENRES},
        "minYear": {"type": "integer", "min": 1990, "max": current_year},
        "maxYear": {"type": "integer", "min": 1990, "max": current_year},
        "Status": {"type": "single", "options": VALID_STATUS},
        "Order": {"type": "single", "options": VALID_ORDERS},
        "Letter": {"type": "single", "options": VALID_LETTERS},
        "Page": {"type": "integer", "min": 1},
    }

    # Guardar los filtros en la base de datos
    #save_filters(filters_data, db)

    return filters_data