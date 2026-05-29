from sqlalchemy import Column, Integer, String, Boolean, DateTime
from db import Base
from datetime import datetime


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=True)
    album = Column(String(255), nullable=True)
    path = Column(String(1024), unique=True, nullable=False)
    duration = Column(Integer, nullable=True)
    # Indique si le fichier a déjà été scanné par le tagger
    scanned = Column(Boolean, default=False, nullable=False)
    # Indique si le tagger a réussi à mettre à jour les métadonnées
    tagged = Column(Boolean, default=False, nullable=False)
    # Nombre de fois joué (statistiques)
    play_count = Column(Integer, default=0, nullable=False)
    # Dernière date de lecture
    last_played = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Track id={self.id} title={self.title!r} path={self.path!r}>"
