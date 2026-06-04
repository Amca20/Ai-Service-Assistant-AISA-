from app import app
from models import db, Admin, Lecturer, LecturerAlias

with app.app_context():
    db.drop_all()
    db.create_all()

    # 1. Create Admin
    admin = Admin(username="admin", password="password123")
    db.session.add(admin)

    # 2. Create Lecturer (YOUR EMAIL)
    dr_azirah = Lecturer(
        name="Dr. Azirah", 
        email="danishbmohdrafid@gmail.com", 
        room_id="Room_101"
    )
    db.session.add(dr_azirah)
    db.session.commit()

    # 3. Create ROBUST Aliases
    # Added "dr azira", "dr. azira", "doctor azira" to ensure it matches!
    aliases = [
        "azira", "asira", "azirah", 
        "miss azirah", "madam azirah", 
        "dr azira", "dr. azira", "doctor azira",
        "dr azirah", "dr. azirah"
    ]
    
    for a in aliases:
        new_alias = LecturerAlias(alias=a, lecturer_id=dr_azirah.id)
        db.session.add(new_alias)

    db.session.commit()
    print("SUCCESS: Database updated with better aliases.")