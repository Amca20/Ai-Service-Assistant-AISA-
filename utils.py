# utils.py
from models import Lecturer, LecturerAlias
from sqlalchemy import func

def find_lecturer_by_fuzzy_name(spoken_name):
    """
    1. Tries to match exact name.
    2. Tries to match known aliases.
    3. Returns the Lecturer object or None.
    """
    if not spoken_name:
        return None
    
    clean_name = spoken_name.lower().strip()

    # 1. Try Exact Match on Real Name
    lecturer = Lecturer.query.filter(func.lower(Lecturer.name) == clean_name).first()
    if lecturer:
        return lecturer

    # 2. Try Aliases (The "Dr Azirah" solution)
    # Checks if 'clean_name' exists in the alias table
    found_alias = LecturerAlias.query.filter(func.lower(LecturerAlias.alias) == clean_name).first()
    
    if found_alias:
        return found_alias.lecturer
        
    return None