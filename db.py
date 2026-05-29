import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Charger .env si présent
load_dotenv()

# Par défaut utiliser SQLite local pour le développement
# Possibilité d'override via la variable d'environnement DATABASE_URL
# SQLite example: sqlite:///./laser.db
# MySQL example: mysql+pymysql://user:pass@host:3306/db
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///./laser.db"

# Pour SQLite, fournir connect_args requis
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, pool_pre_ping=True)
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db():
    """Importe les modèles et crée les tables si nécessaire."""
    # Importer les modules de modèles pour enregistrer les classes sur Base
    try:
        import models  # noqa: F401
    except Exception:
        # Si import échoue, on laisse l'exception remonter pour diagnostics
        raise

    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Contexte générateur pour obtenir une session SQLAlchemy."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
